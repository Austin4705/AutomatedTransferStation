import omero
from omero.gateway import BlitzGateway
from omero.model import DatasetI, ProjectI, ImageI
from omero.rtypes import rstring, rlong, rint

from PIL import Image
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from dotenv import load_dotenv
import json
import numpy as np
import os
from datetime import datetime
import logging
from multiprocessing import Pool
import cv2

# import camera
# from transfer_station import Transfer_Station
# from cv_functions import CV_Functions
# from GMMDetector.structures import Flake
# import packet_handlers

class Image_Container:
    """
    This class is used to store images.
    """

    def __init__(self, transfer_station):
        self.connect_to_omero(os.getenv('OMERO_HOST'), os.getenv('OMERO_USERNAME'), os.getenv('OMERO_PASSWORD'))
        self.transfer_station = transfer_station

    def connect_to_omero(self, host: str, username: str, password: str, port: int = 4064) -> BlitzGateway:
        logging.getLogger("omero").setLevel(logging.ERROR)
        logging.getLogger("omero.gateway").setLevel(logging.ERROR)
        logging.getLogger("omero.sessions").setLevel(logging.ERROR)
        logging.getLogger("omero.cli").setLevel(logging.ERROR)
        self.conn = BlitzGateway(username, password, host=host, port=port, secure=True)
        if not self.conn.connect():
            raise ConnectionError("Failed to connect to OMERO server")
    
    def disconnect_from_omero(self):
        if self.conn:
            self.conn.close()

    def create_dataset(self, name: str, description: Optional[str] = None, project_id: Optional[int] = None) -> int:
        dataset = omero.model.DatasetI()
        dataset.setName(rstring(name))
        if description:
            dataset.setDescription(rstring(description))
        dataset = self.conn.getUpdateService().saveAndReturnObject(dataset)
        dataset_id = dataset.getId().getValue()
        
        if project_id:
            link = omero.model.ProjectDatasetLinkI()
            link.setParent(omero.model.ProjectI(project_id, False))
            link.setChild(omero.model.DatasetI(dataset_id, False))
            self.conn.getUpdateService().saveObject(link)
        
        return dataset_id

    def create_project(self, name: str, description: Optional[str] = None) -> int:
        project = omero.model.ProjectI()
        project.setName(rstring(name))
        if description:
            project.setDescription(rstring(description))
        project = self.conn.getUpdateService().saveAndReturnObject(project)
        return project.getId().getValue()


        
    def upload_image(self, img_array: np.ndarray | list | tuple, dataset_id: Optional[int] = None, image_name: str = "image", metadata: Optional[Dict] = None) -> int:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        img_array = np.transpose(img_array, (2, 0, 1))  # Convert to (3, Y, X)
        size_c, size_y, size_x = img_array.shape

        img_copy = np.ascontiguousarray(img_array)
        def plane_gen():
            for c in range(size_c):
                plane = np.ascontiguousarray(img_copy[c, :, :])
                yield plane

        image = self.conn.createImageFromNumpySeq(
            plane_gen(), image_name, 1, size_c, 1,
            dataset=None
        )
        image_id = image.getId()

        if dataset_id:
            link = omero.model.DatasetImageLinkI()
            link.setParent(omero.model.DatasetI(dataset_id, False))
            link.setChild(omero.model.ImageI(image_id, False))
            self.conn.getUpdateService().saveObject(link)

        if metadata:
            self.add_metadata(image_id, metadata)

        return image_id

    
    def download_image(self, image_id: int) -> np.ndarray:
        """
        Returns:
            numpy array in (Y, X, 3) format (same as cv2.imread - BGR format). Assumes the png on the server is in the correct formatj.
        """

        image = self.conn.getObject("Image", image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")
        pixels = image.getPrimaryPixels()
        sizeZ = image.getSizeZ()
        sizeC = image.getSizeC()
        sizeT = image.getSizeT()
        sizeY = image.getSizeY()
        sizeX = image.getSizeX()
        data = np.zeros((sizeX, sizeY, sizeC), dtype=np.uint8)
        for c in range(sizeC):
            plane = pixels.getPlane(0, c, 0)
            data[:, :, c] = plane

        return data
       
    
    def metadata_serialize(self, image_id: int) -> Dict:
        image = self.conn.getObject("Image", image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")
        
        metadata = {
            'id': image.getId(),
            'name': image.getName(),
            'description': image.getDescription(),
            'acquisition_date': str(image.getAcquisitionDate()) if image.getAcquisitionDate() else None,
            'owner': image.getOwnerFullName(),
            'dimensions': {
                'x': image.getSizeX(), 'y': image.getSizeY(), 'z': image.getSizeZ(),
                'c': image.getSizeC(), 't': image.getSizeT(),
            },
            'pixel_size': {
                'x': image.getPixelSizeX(), 'y': image.getPixelSizeY(), 'z': image.getPixelSizeZ(),
            },
            'channels': [{'label': ch.getLabel(), 'color': ch.getColor().getHtml() if ch.getColor() else None, 
                        'wavelength': ch.getEmissionWave()} for ch in image.getChannels()],
            'key_value_pairs': {},
            'tags': [],
            'comments': [],
        }
        
        for ann in image.listAnnotations():
            if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                for key, value in ann.getValue():
                    metadata['key_value_pairs'][key] = value
            elif isinstance(ann, omero.gateway.TagAnnotationWrapper):
                metadata['tags'].append(ann.getValue())
            elif isinstance(ann, omero.gateway.CommentAnnotationWrapper):
                metadata['comments'].append(ann.getValue())
        
        return metadata

    def apply_metadata_to_image(self, image_id: int, metadata: Dict):
        if metadata.get('key_value_pairs'):
            map_ann = omero.gateway.MapAnnotationWrapper(self.conn)
            namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
            map_ann.setNs(namespace)
            map_ann.setValue(list(metadata['key_value_pairs'].items()))
            map_ann.save()

            image = self.conn.getObject("Image", image_id)
            image.linkAnnotation(map_ann)

        for tag_value in metadata.get('tags', []):
            tag_ann = omero.gateway.TagAnnotationWrapper(self.conn)
            tag_ann.setValue(tag_value)
            tag_ann.save()

            image = self.conn.getObject("Image", image_id)
            image.linkAnnotation(tag_ann)

        # Add comments
        for comment_value in metadata.get('comments', []):
            comment_ann = omero.gateway.CommentAnnotationWrapper(self.conn)
            comment_ann.setValue(comment_value)
            comment_ann.save()

            image = self.conn.getObject("Image", image_id)
            image.linkAnnotation(comment_ann)

    def dataset_serialize(self, dataset_id: int) -> Dict:
        dataset = self.conn.getObject("Dataset", dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        metadata = {
            'id': dataset.getId(),
            'name': dataset.getName(),
            'description': dataset.getDescription(),
            'owner': dataset.getOwnerFullName(),
            'image_count': dataset.countChildren(),
            'images': [{'id': img.getId(), 'name': img.getName()} for img in dataset.listChildren()],
            'key_value_pairs': {},
            'tags': [],
        }
        
        for ann in dataset.listAnnotations():
            if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                for key, value in ann.getValue():
                    metadata['key_value_pairs'][key] = value
            elif isinstance(ann, omero.gateway.TagAnnotationWrapper):
                metadata['tags'].append(ann.getValue())
        
        return metadata

    def apply_metadata_to_dataset(self, dataset_id: int, metadata: Dict):
        pass

    def generate_image_output(self):
        pass
        # for image_metadata in self.metadata.get("searched"):
        #     image = self.load_image(image_metadata["name"], image_metadata["wafer_id"])
        #     flakes = [
        #         Flake(
        #             thickness=flake.get("thickness"),
        #             size=flake.get("size"), 
        #             false_positive_probability=flake.get("false_positive_probability"),
        #             center=flake.get("center"),
        #             mask=cv2.imread(os.path.join(self.directory_flake_masks, flake.get("mask")), cv2.IMREAD_GRAYSCALE),
        #             max_sidelength=flake.get("max_sidelength"),  # Default values for required parameters
        #             min_sidelength=flake.get("min_sidelength"),  # Default values for required parameters
        #             mean_contrast=flake.get("mean_contrast")  #
        #         )
        #         for flake in image_metadata.get("flakes", [])
        #     ]
        #     # image_data = CV_Functions.visualise_flakes(flakes, image, 0.5)
        #     image_data = image
        #     # Add wafer and position text
        #     cv2.putText(
        #         image_data,
        #         f"Wafer: {image_metadata['wafer_id']}", 
        #         (image_data.shape[1] - 300, 30),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         1,
        #         (255, 255, 255),
        #         2
        #     )
        #     cv2.putText(
        #         image_data,
        #         f"Image Number: {image_metadata['image_id']}", 
        #         (image_data.shape[1] - 300, 60),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         1,
        #         (255, 255, 255),
        #         2
        #     )
        #     cv2.putText(
        #         image_data,
        #         f"x: {image_metadata['x']} y: {image_metadata['y']}", 
        #         (image_data.shape[1] - 300, 90),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         1,
        #         (255, 255, 255),
        #         2
        #     )
        #     cv2.imwrite(os.path.join(self.directory_searched, image_metadata["name"]), image_data)
