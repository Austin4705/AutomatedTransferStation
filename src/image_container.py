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

from logger import Logger

class Image_Container:
    """
    This class is used to store images.
    """

    def __init__(self):
        self.connect_to_omero(os.getenv('OMERO_HOST'), os.getenv('OMERO_USERNAME'), os.getenv('OMERO_PASSWORD'))
        self.wafers = {}
        self.wafers["default_location"] = self.load_or_create_chip_by_name("default_location")
        self.active_chip_id = self.wafers["default_location"]

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


        
    def upload_image(self, img_array: np.ndarray | list | tuple, dataset_id: Optional[int] = None, image_name: str = "image", metadata: Optional[Dict] = None, include_time_name: bool = True, max_dimension: int = 2048, save_locally: bool = False) -> int:

        height, width = img_array.shape[:2]
        if max_dimension is not None and max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_AREA)
            Logger.log(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            height, width = new_height, new_width
        
        if include_time_name:
            image_name = f"{image_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        
        if save_locally:
            cv2.imwrite(
                f"../Photos/{image_name}.png",
                img_array,
            )

        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        img_array = np.transpose(img_array, (2, 0, 1))  # Convert to (3, Y, X)
        size_c, size_y, size_x = img_array.shape
        size_z, size_t = 1, 1

        img_copy = np.ascontiguousarray(img_array)
        def plane_gen():
            for c in range(size_c):
                plane = np.ascontiguousarray(img_copy[c, :, :])
                yield plane

        image = self.conn.createImageFromNumpySeq(
            plane_gen(), image_name, size_z, size_c, size_t,
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

        # Set rendering settings to use full 0-255 range for all channels
        self.set_rendering_settings(image_id)

        return image_id

    def set_rendering_settings(self, image_id: int):
        """Set rendering settings for an image to use full 0-255 range for all channels"""
        image = self.conn.getObject("Image", image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Set rendering settings for each channel
        image.setActiveChannels(list(range(1, image.getSizeC() + 1)))
        for idx, channel in enumerate(image.getChannels()):
            # Set the rendering window to 0-255 for each channel
            channel.setWindowStart(0.0)
            channel.setWindowEnd(255.0)

        # Save the rendering settings
        image.saveDefaults()
    
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
        data = np.zeros((sizeY, sizeX, sizeC), dtype=np.uint8)
        for c in range(sizeC):
            plane = pixels.getPlane(0, c, 0)
            data[:, :, c] = plane
        # Data from Omero is in RGB format, convert to BGR for OpenCV
        return cv2.cvtColor(np.ascontiguousarray(data), cv2.COLOR_RGB2BGR)
        # return np.ascontiguousarray(data)
       
    
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
        image = self.conn.getObject("Image", image_id)

        if metadata.get('key_value_pairs'):
            # Convert all values to strings for OMERO MapAnnotation
            key_value_pairs = [(str(k), str(v)) for k, v in metadata['key_value_pairs'].items()]

            existing_map_ann = None
            for ann in image.listAnnotations():
                if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                    existing_map_ann = ann
                    break
            if existing_map_ann:
                existing_map_ann.setValue(key_value_pairs)
                existing_map_ann.save()
            else:
                map_ann = omero.gateway.MapAnnotationWrapper(self.conn)
                namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
                map_ann.setNs(namespace)
                map_ann.setValue(key_value_pairs)
                map_ann.save()
                image.linkAnnotation(map_ann)

        if 'tags' in metadata:
            existing_tags = [ann for ann in image.listAnnotations()
                           if isinstance(ann, omero.gateway.TagAnnotationWrapper)]
            new_tag_values = metadata.get('tags', [])
            for i, tag_value in enumerate(new_tag_values):
                if i < len(existing_tags):
                    existing_tags[i].setValue(tag_value)
                    existing_tags[i].save()
                else:
                    tag_ann = omero.gateway.TagAnnotationWrapper(self.conn)
                    tag_ann.setValue(tag_value)
                    tag_ann.save()
                    image.linkAnnotation(tag_ann)
            for j in range(len(new_tag_values), len(existing_tags)):
                image.unlinkAnnotation(existing_tags[j])

        if 'comments' in metadata:
            existing_comments = [ann for ann in image.listAnnotations()
                               if isinstance(ann, omero.gateway.CommentAnnotationWrapper)]
            new_comment_values = metadata.get('comments', [])
            for i, comment_value in enumerate(new_comment_values):
                if i < len(existing_comments):
                    existing_comments[i].setValue(comment_value)
                    existing_comments[i].save()
                else:
                    comment_ann = omero.gateway.CommentAnnotationWrapper(self.conn)
                    comment_ann.setValue(comment_value)
                    comment_ann.save()
                    image.linkAnnotation(comment_ann)
            for j in range(len(new_comment_values), len(existing_comments)):
                image.unlinkAnnotation(existing_comments[j])

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
            # 'images': [{'id': img.getId(), 'name': img.getName()} for img in dataset.listChildren()],
            'key_value_pairs': {},
            'tags': [],
            'comments': [],
        }
        
        for ann in dataset.listAnnotations():
            if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                for key, value in ann.getValue():
                    metadata['key_value_pairs'][key] = value
            elif isinstance(ann, omero.gateway.TagAnnotationWrapper):
                metadata['tags'].append(ann.getValue())
        
        return metadata

    def apply_metadata_to_dataset(self, dataset_id: int, metadata: Dict):
        dataset = self.conn.getObject("Dataset", dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        if metadata.get('key_value_pairs'):
            # Convert all values to strings for OMERO MapAnnotation
            key_value_pairs = [(str(k), str(v)) for k, v in metadata['key_value_pairs'].items()]

            existing_map_ann = None
            for ann in dataset.listAnnotations():
                if isinstance(ann, omero.gateway.MapAnnotationWrapper):
                    existing_map_ann = ann
                    break

            if existing_map_ann:
                existing_map_ann.setValue(key_value_pairs)
                existing_map_ann.save()
            else:
                map_ann = omero.gateway.MapAnnotationWrapper(self.conn)
                namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
                map_ann.setNs(namespace)
                map_ann.setValue(key_value_pairs)
                map_ann.save()
                dataset.linkAnnotation(map_ann)

        if 'tags' in metadata:
            existing_tags = [ann for ann in dataset.listAnnotations()
                           if isinstance(ann, omero.gateway.TagAnnotationWrapper)]
            new_tag_values = metadata.get('tags', [])
            for i, tag_value in enumerate(new_tag_values):
                if i < len(existing_tags):
                    existing_tags[i].setValue(tag_value)
                    existing_tags[i].save()
                else:
                    tag_ann = omero.gateway.TagAnnotationWrapper(self.conn)
                    tag_ann.setValue(tag_value)
                    tag_ann.save()
                    dataset.linkAnnotation(tag_ann)
            for j in range(len(new_tag_values), len(existing_tags)):
                dataset.unlinkAnnotation(existing_tags[j])

    def get_dataset_by_name(self, project_id: int, dataset_name: str) -> Optional[int]:
        project = self.conn.getObject("Project", project_id)
        if not project:
            return None

        for dataset in project.listChildren():
            if dataset.getName() == dataset_name:
                return dataset.getId()

        return None

    def load_chip(self, chip_id: int):
        project = self.conn.getObject("Project", chip_id)
        if not project:
            return
        
        chip_name = project.getName()
        project_id = project.getId()
        self.wafers[chip_id] = {
            'id': chip_id,
            'name': chip_name,
            'dataset_snapshot_id': self.get_dataset_by_name(project_id, "snapshot"),
            'dataset_flake_hunted_snapshot_id': self.get_dataset_by_name(project_id, "flake_hunted_snapshot")
        }

    def create_chip(self, chip_name: str):
        chip_id = self.create_project(chip_name)
        
        dataset_snapshot_id = self.create_dataset("snapshot", project_id=chip_id)
        dataset_flake_hunted_snapshot_id = self.create_dataset("flake_hunted_snapshot", project_id=chip_id)
        self.wafers[chip_id] = {
            'id': chip_id,
            'name': chip_name,
            'dataset_snapshot_id': dataset_snapshot_id,
            'dataset_flake_hunted_snapshot_id': dataset_flake_hunted_snapshot_id
        }
        return chip_id

    def save_snapshot(self, chip_id: int, snapshot: np.ndarray):
        return self.upload_image(snapshot, self.wafers[chip_id]['dataset_snapshot_id'])

    def save_flake_hunted_snapshot(self, chip_id: int, snapshot: np.ndarray):
        return self.upload_image(snapshot, self.wafers[chip_id]['dataset_flake_hunted_snapshot_id'])

    def load_or_create_chip_by_name(self, chip_name: str) -> int:
        for project in self.conn.getObjects("Project"):
            if project.getName() == chip_name:
                chip_id = project.getId()
                if chip_id not in self.wafers:
                    self.load_chip(chip_id)
                return chip_id

        # If not found, create a new chip
        chip_id = self.create_chip(chip_name)
        return chip_id

    def create_new_collection(self, chip_id: int, collection_name: str="default"):
        if collection_name == "default":
            collection_name = f"collection_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        collection_id = self.create_dataset(collection_name, project_id=chip_id)
        return collection_id
