import json
import numpy as np
import os
from datetime import datetime
from multiprocessing import Pool
import cv2
from camera import Camera
from transfer_station import Transfer_Station
from cvFunctions import CVFunctions
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
        self.directory_flake_masks = os.path.join(self.directory, "flake_masks")
        os.makedirs(self.directory_images, exist_ok=True)
        os.makedirs(self.directory_searched, exist_ok=True)
        os.makedirs(self.directory_flake_masks, exist_ok=True)

        metadata_path = os.path.join(self.directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.metadata = dict(json.load(f)) 
        else:
            self.metadata = dict()
            self.metadata["images"] = []
            self.metadata["searched"] = []
            self.metadata["metametadata"] = []

        self.flake_counter = 0
        # self.images = dict()
        # self.load_container()

    def load_container(self):
        for image in self.metadata["images"]:
            name = image["name"]
            image_path = os.path.join(self.directory_images, name)
            self.images[name] = image

    def load_sent_data(self, data: dict):
        self.metadata["metametadata"].append(data)
        self.save_metadata()

    def add_image(self, camera_id: int):
        camera = Camera.global_list[camera_id]
        frame = camera.snap_image()
        image_name = f"{camera_id}-{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.jpg"
        image_path = os.path.join(self.directory_images, image_name)
        cv2.imwrite(image_path, frame)

        self.metadata["images"].append({
            "name": image_name,
            "camera_id": camera_id,
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

    def load_image(self, image_name: str):
        image_path = os.path.join(self.directory_images, image_name)
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

    def new_flake(self):
        pass

    def search_images(self):
        # Running multithreaded pool to search images
        with Pool(5) as pool:
            results = pool.map(self.search_image, self.metadata.get("images"))
        print("Finished Hunting")
        # Add flake data to each image in metadata
        for image, flake_data in zip(self.metadata.get("images"), results):
            counter = 0
            for flake in flake_data:
                mask_name = f"{image['name']}-{counter}.png"
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
            if flake_data:
                print(f"flake data is {flake_data}")
                self.metadata["searched"].append(image)
        self.save_metadata()

    def generate_image_output(self):
        for image_metadata in self.metadata.get("searched"):
            image_path = os.path.join(self.directory_images, image_metadata["name"])
            image = self.load_image(image_metadata["name"])
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
            cv2.imwrite(os.path.join(self.directory_searched, image_metadata["name"]), image_data)

    def search_image(self, data):
        image_name = data["name"]
        image_data = self.load_image(image_name)
        # Run CV search
        print(data)
        flake_data = CVFunctions.run_searching(image_data)
        return flake_data

    def show_images(self):
        for image in self.metadata["searched"]:
            image_path = os.path.join(self.directory_images, image["name"])
            image = self.load_image(image_path)
            cv2.imshow("Image", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
