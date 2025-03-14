import json
import numpy as np
import os
from datetime import datetime
from multiprocessing import Pool
import cv2
from camera import Camera
from transfer_station import Transfer_Station
from cvFunctions import CVFunctions
import packet_handlers
from GMMDetector.structures import Flake

class Image_Container:
    """
    This class is used to store images.
    """
    IMAGE_REPO_NAME = "../images"

    # Overloading constructors to handle different types of initialization
    # Other than the directory name all data is stored in the metadata.json file
    def __init__(self, transfer_station: Transfer_Station, directory: str = None):
        if directory is None:
            self.directory = os.path.join(Image_Container.IMAGE_REPO_NAME, datetime.now().strftime('%d-%m-%Y-%H-%M-%S'))
        else:
            self.directory = os.path.join(Image_Container.IMAGE_REPO_NAME, directory)
        os.makedirs(self.directory, exist_ok=True)
        self.transfer_station = transfer_station
        self.directory_images = os.path.join(self.directory, "images")
        self.directory_searched = os.path.join(self.directory, "searched")
        self.directory_flake_masks = os.path.join(self.directory, "wafer_masks")
        os.makedirs(self.directory_images, exist_ok=True)
        os.makedirs(self.directory_searched, exist_ok=True)
        os.makedirs(self.directory_flake_masks, exist_ok=True)

        metadata_path = os.path.join(self.directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.metadata = dict(json.load(f)) 
        else:
            self.metadata = dict()
            self.metadata["wafers"] = []
            self.metadata["searched"] = []
            self.metadata["metametadata"] = []

        self.wafer_counter = 0
        self.image_counter = 0
        self.scanned_counter = 0

    def load_sent_data(self, data: dict):
        self.metadata["metametadata"].append(data)
        self.save_metadata()

    def add_image(self, camera_id: int):
        self.image_counter += 1
        camera = Camera.global_list[camera_id]
        frame = camera.snap_image()
        image_name = f"{camera_id}-{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.jpg"
        wafer_path = os.path.join(self.directory_images, f"wafer_{self.wafer_counter}")
        image_path = os.path.join(wafer_path, image_name)
        cv2.imwrite(image_path, frame)
        self.metadata["wafers"][-1].append({
            "wafer_id": self.wafer_counter,
            "name": image_name,
            "camera_id": camera_id,
            "image_id": self.image_counter,
            "x": self.transfer_station.posX(),
            "y": self.transfer_station.posY(),
            "flakes": []
        })

        self.save_metadata()

    def save_metadata(self):
        metadata_path = os.path.join(self.directory, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f) 
    
    def load_metadata(self, directory: str):
        with open(f"{directory}/metadata.json", 'r') as f:
            self.metadata = json.load(f)

    def load_image(self, image_name: str, wafer_id: int):
        image_path = os.path.join(self.directory_images, f"wafer_{wafer_id}", image_name)
        try:
            if os.path.exists(image_path):
                # Load image using OpenCV
                image_data = cv2.imread(image_path)
                if image_data is None:
                    print(f"Failed to load image {image_name}")
                    return np.zeros((512, 512, 3), dtype=np.uint8)
                return image_data
            else:
                print(f"Image {image_name} not found")
                return np.zeros((512, 512, 3), dtype=np.uint8)
        except Exception as e:
            print(f"Error checking image path: {e}")
            return None

    def new_wafer(self):
        self.wafer_counter += 1
        self.metadata["wafers"].append([])
        os.makedirs(os.path.join(self.directory_images, f"wafer_{self.wafer_counter}"), exist_ok=True)
        self.image_counter = 0

    def search_and_save_wafer(self):
        self.search_images()
        self.generate_image_output()

    def search_images(self):
        self.wafer_counter = 0
        for wafer in self.metadata["wafers"]:
            self.scanned_counter = 0
            self.wafer_counter += 1
            # Running multithreaded pool to search images
            packet_handlers.PacketCommander.send_message(f"Searching in wafer {self.wafer_counter}")
            with Pool(5) as pool:
                results = pool.map(self.search_image, wafer)
            packet_handlers.PacketCommander.send_message(f"Finished Hunting wafer {self.wafer_counter}")
            # Add flake data to each image in metadata
            for image, flake_data in zip(wafer, results):
                counter = 0
                for flake in flake_data:
                    mask_name = f"Wafer_{self.wafer_counter}-Image_{image['name']}-Flake_{counter}.png"
                    counter += 1
                    cv2.imwrite(os.path.join(self.directory_flake_masks, mask_name), flake.mask)
                    image["flakes"].append(
                        {
                            "thickness": flake.thickness,
                            "size": flake.size,
                            "false_positive_probability": flake.false_positive_probability,
                            "center": list(flake.center),
                            "max_sidelength": flake.max_sidelength,
                            "min_sidelength": flake.min_sidelength,
                            "mean_contrast": flake.mean_contrast,
                            "mask": mask_name
                        })
                if flake_data.any():
                    # print(f"flake data is {flake_data}")
                    self.metadata["searched"].append(image)
                self.save_metadata()

    def search_image(self, data):
        image_name = data["name"]

        image_data = self.load_image(image_name, data["wafer_id"])
        # Run CV search
        flake_data = CVFunctions.run_searching(image_data)
        self.update_scanned_counter(data["image_id"])
        return flake_data

    def update_scanned_counter(self, image_id):
        if image_id > self.scanned_counter:
            self.scanned_counter = image_id
            print(f"Scanned counter is {self.scanned_counter} out of {len(self.metadata['wafers'][self.wafer_counter-1])}")

    def generate_image_output(self):
        for image_metadata in self.metadata.get("searched"):
            image = self.load_image(image_metadata["name"], image_metadata["wafer_id"])
            flakes = [
                Flake(
                    thickness=flake.get("thickness"),
                    size=flake.get("size"), 
                    false_positive_probability=flake.get("false_positive_probability"),
                    center=flake.get("center"),
                    mask=cv2.imread(os.path.join(self.directory_flake_masks, flake.get("mask")), cv2.IMREAD_GRAYSCALE),
                    max_sidelength=flake.get("max_sidelength"),  # Default values for required parameters
                    min_sidelength=flake.get("min_sidelength"),  # Default values for required parameters
                    mean_contrast=flake.get("mean_contrast")  #
                )
                for flake in image_metadata.get("flakes", [])
            ]
            image_data = CVFunctions.visualise_flakes(flakes, image, 0.5)
            # Add wafer and position text
            cv2.putText(
                image_data,
                f"Wafer: {image_metadata['wafer_id']}", 
                (image_data.shape[1] - 300, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                image_data,
                f"Image Number: {image_metadata['image_id']}", 
                (image_data.shape[1] - 300, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                image_data,
                f"x: {image_metadata['x']} y: {image_metadata['y']}", 
                (image_data.shape[1] - 300, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.imwrite(os.path.join(self.directory_searched, image_metadata["name"]), image_data)

    def show_images(self):
        for image in self.metadata["searched"]:
            image_path = os.path.join(self.directory_images, image["name"])
            image = self.load_image(image_path)
            cv2.imshow("Image", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
