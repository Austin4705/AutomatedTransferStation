import cv2
from datetime import datetime
import os

class camera(object):
    global_list = dict()
    IMAGE_REPO_NAME = "images"
    def __init__(self, cameraId):
        self.video = cv2.VideoCapture(cameraId)
        camera.global_list[cameraId] = self
        self.camera_id = cameraId
        str_id = str(cameraId)
        str_dateTime = str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S"))
        str_concat = str_id+"-"+str_dateTime
        self.name = ("camera"+str_concat)
        print(self.name)
        self.create_image_repo()
        self.get_frame()
        self.capture_image(0,1,2)

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
        filename = f"{i}-{j}-{c}-camera{self.camera_id}"
        image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(camera.IMAGE_REPO_NAME+"/"+self.name+"/"+filename+".png", image)



    def get_frame(self):
        ret, self.frame = self.video.read()
    
        # DO WHAT YOU WANT WITH TENSORFLOW / KERAS AND OPENCV

        ret, self.jpeg = cv2.imencode('.jpg', self.frame)

        return self.jpeg.tobytes()
    
    def generate_video(camera):
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
