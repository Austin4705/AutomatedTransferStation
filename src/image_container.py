import json
import numpy as np
import os
from datetime import datetime
from multiprocessing import Pool
import cv2
from camera import Camera
from transfer_station import Transfer_Station
from cvFunctions import CVFunctions

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
            self.directory = directory
        os.makedirs(self.directory, exist_ok=True)
        self.transfer_station = transfer_station
        self.directory_images = os.path.join(self.directory, "images")
        self.directory_searched = os.path.join(self.directory, "searched")
        os.makedirs(self.directory_images, exist_ok=True)
        os.makedirs(self.directory_searched, exist_ok=True)

        metadata_path = os.path.join(self.directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.metadata = dict(json.load(f)) 
        else:
            self.metadata = dict()
            self.metadata["images"] = []
            self.metadata["searched"] = []

        # self.images = dict()
        # self.load_container()

    def load_container(self):
        for image in self.metadata["images"]:
            name = image["name"]
            image_path = os.path.join(self.directory_images, name)
            self.images[name] = image

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
            "y": self.transfer_station.posY()
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
                # Assuming the image is in a format that can be loaded by numpy
                image_data = np.load(image_path)
                return image_data
            else:
                print(f"Image {image_name} not found")
                return np.zeros((512, 512, 3), dtype=np.uint8)
        except Exception as e:
            print(f"Error checking image path: {e}")
            return None


    def search_images(self):
        # Running multithreaded pool to search images
        with Pool(5) as pool:
            results = pool.map(self.search_image, self.metadata.get("images", []))

        # Add flake data to each image in metadata
        for image, flake_data in zip(self.metadata.get("images", []), results):
            image["flakes"] = [
                {
                    "thickness": flake.thickness,
                    "size": flake.size,
                    "confidence": 1 - flake.false_positive_probability,
                    "center": flake.center.tolist()
                }
                for flake in flake_data
            ]
            if flake_data is not None:
                self.metadata["searched"].append(image)
        self.save_metadata()


    def search_image(self, image):
        try:
            image_name = image["name"]
            
            # Load the image
            image_data = self.load_image(image_name)
            if image_data is None:
                return None
        except Exception as e:
            print(f"Error searching image {image.get('name', 'unknown')}: {e}")
            return None     

        # Run CV search
        flake_data = CVFunctions.run_searching(image_data)
        return flake_data

    def show_images(self):
        for image in self.metadata["searched"]:
            image_path = os.path.join(self.directory_images, image["name"])
            image = self.load_image(image_path)
            cv2.imshow("Image", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
