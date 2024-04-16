import cv2

class Image_Container:
    PATH_NAME = "images"

    def __init__(self, folder_name, camera, name_metric) -> None:
        self.camera = camera
        self.folder_name = folder_name
        self.map = dict
        self.name_metric = name_metric
        # Make Dir images/foldername
        pass
    def takeImage(self):
        photo = self.camera
        self.map[self.name_metric()] = photo
        return photo
        
    def get_photo(self):
        pass
        