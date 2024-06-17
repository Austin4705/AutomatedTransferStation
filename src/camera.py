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
            

    def cvImage(img):
        # Convert to YCrCb Channel and extract cb channel
        imgYCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCR_CB)
        channel = imgYCrCb[:,:,2]

        ret, threshold = cv2.threshold(channel, 160,  255, cv2.THRESH_BINARY)


        result = img.copy()
        contours, hierarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # contours = contours[0] if len(contours) == 2 else contours[1]
        cv2.drawContours(result, contours, -1, (0, 255, 0), 3) 

        for cont in contours:
            maxX = cont[0][0]
            maxY = cont[0][0]
            minX = cont[0][0]
            minY = cont[0][0]
            for point in cont:
                pt = point[0]
                if pt[0] > maxX[0]:
                    maxX = pt
                elif pt[0] == maxX[0]:
                    maxX = [pt[0], max(pt[1], maxX[1])]

                if pt[0] < minX[0]:
                    minX = pt
                elif pt[0] == minX[0]:
                    minX = [pt[0], min(pt[1], minX[1])]

                if pt[1] > maxY[1]:
                    maxY = pt
                elif pt[1] == maxY[1]:
                    maxY = [max(pt[0], maxY[0]), pt[1]]

                if pt[1] < minY[1]:
                    minY = pt
                elif pt[1] == minY[1]:
                    minY = [min(pt[0], maxY[0]), pt[1]]
            cv2.line(result, minX, minY, [0,255,0], 10)
            cv2.line(result, minY, maxX, [0,255,0], 10)
            cv2.line(result, maxX, maxY, [0,255,0], 10)
            cv2.line(result, maxY, minX, [0,255,0], 10)
            # print(f"{minX}, {minY}, {maxX}, {maxY}")
            return minX, minY, maxX, maxY 
