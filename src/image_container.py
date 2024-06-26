import cv2
from camera import Camera
from datetime import datetime
import os 

class Image_Container:
    IMAGE_REPO_NAME = "images"
    
    def __init__(self, cameraId) -> None:
        self.name = ("camera"+str(cameraId)+"-"+str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S")))
        self.camera = Camera.global_list[cameraId]    
        self.create_image_repo()

    def create_image_repo(self):
            # create the directories
            try:
                os.mkdir(Image_Container.IMAGE_REPO_NAME)
            except OSError as error:
                pass
            try:
                os.mkdir(Image_Container.IMAGE_REPO_NAME+"/"+self.name)
            except OSError as error:
                pass

    def capture_image(self, i, j, c):
        self.camera.get_frame()
        filename = f"{i}-{j}-camera"
        cv2.imwrite("../"+Image_Container.IMAGE_REPO_NAME+"/"+self.name+"/"+filename+".png", self.camera.frame)

    def get_photo(self):
        pass
        