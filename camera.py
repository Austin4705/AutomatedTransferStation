import cv2
from datetime import datetime
import os

class camera:
    global_list = dict()
    IMAGE_REPO_NAME = "images"
    def __init__(self, cameraId):
        self.video = cv2.VideoCapture(cameraId, cv2.CAP_DSHOW)
        camera.global_list[cameraId] = self
        self.camera_id = cameraId
        self.get_frame()

    def __del__(self):
        self.video.release() 

    def get_frame(self):
        ret, self.frame = self.video.read()
        ret, self.jpeg = cv2.imencode('.jpg', self.frame)
        return self.jpeg.tobytes()
    
    def generate_video(camera):
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
