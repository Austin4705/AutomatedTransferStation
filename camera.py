import cv2
from datetime import datetime
import os

class camera(object):
    global_list = dict()
    IMAGE_REPO_NAME = "images"
    def __init__(self, cameraId):
        self.video = cv2.VideoCapture(cameraId, cv2.CAP_DSHOW)
        camera.global_list[cameraId] = self
        self.camera_id = cameraId
        self.name = ("camera"+str(cameraId)+"-"+str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S")))
        self.get_frame()

    def __del__(self):
        self.video.release()        

    def create_image_repo(self):
        # create the directories
        try:
            os.mkdir(camera.IMAGE_REPO_NAME)
        except OSError as error:
            pass
        try:
            os.mkdir(camera.IMAGE_REPO_NAME+"/"+self.name)
        except OSError as error:
            pass
    
    def capture_image(self, i, j, c):
        self.get_frame()
        filename = f"{i}-{j}-camera"
        # image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(camera.IMAGE_REPO_NAME+"/"+self.name+"/"+filename+".png", self.frame)

    def get_frame(self):
        ret, self.frame = self.video.read()
        ret, self.jpeg = cv2.imencode('.jpg', self.frame)
        return self.jpeg.tobytes()
    
    def generate_video(camera):
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
