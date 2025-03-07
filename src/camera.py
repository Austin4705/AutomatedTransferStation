import cv2
from datetime import datetime
import os
from demo_functions import visualise_flakes, remove_vignette
import json
from GMMDetector import MaterialDetector


class Camera:
    global_list = dict()
    IMAGE_REPO_NAME = "images"
    contrast_dict = json.load(open("../contrastDictDir/Graphene_GMM.json", "r"))
    mockImage = cv2.imread("mockImage.png")

    def __init__(self, cameraId):
        self.video = cv2.VideoCapture(cameraId, cv2.CAP_DSHOW)
        if not self.video.isOpened():
            print(f"Error: Could not open camera with ID {cameraId}")
            print(f"Camera status: {self.video.isOpened()}")
            # Try without CAP_DSHOW
            self.video = cv2.VideoCapture(cameraId)
            if not self.video.isOpened():
                print("Error: Still could not open camera without CAP_DSHOW")
                raise RuntimeError(f"Failed to open camera {cameraId}")
        
        # Set some basic properties
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        Camera.global_list[cameraId] = self
        self.camera_id = cameraId
        self.snap_image()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        if not self.video.isOpened():
            print(f"Error: Camera {self.camera_id} is not opened")
            return None
            
        ret, self.frame = self.video.read()
        if not ret:
            print(f"Error: Could not read frame from camera {self.camera_id}")
            return None
            
        print(f"Frame shape: {self.frame.shape if self.frame is not None else 'None'}")
        return self.frame

    def save_image(frame):
        cv2.imwrite(
            f"../{Camera.IMAGE_REPO_NAME}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg",
            frame,
        )

    def snap_image(self):
        self.snapshot_image = Camera.matGMM2DTransform(self.get_frame())
        #  Camera.matGMM2DTransform

    def generate_video(camera):
        while True:
            frame = camera.get_frame()
            # frame = Camera.matGMM2DTransform(frame)
            ret, png = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
            )

    def get_snapped_image(camera):
        ret, png = cv2.imencode(".jpg", camera.snapshot_image)
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    def matGMM2DTransform(img):
        CONFIDENCE_THRESHOLD = 0.5

        model = MaterialDetector(
            contrast_dict=Camera.contrast_dict,
            size_threshold=500,
            standard_deviation_threshold=5,
            used_channels="BGR",
        )

        flakes = model.detect_flakes(img)
        image = visualise_flakes(
            flakes,
            img,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
        return image

    def cvImageBoarderOp(img):
        # Convert to YCrCb Channel and extract cb channel
        imgYCrCb = cv2.cvtColor(img, cv2.COLOR_BGR2YCR_CB)
        channel = imgYCrCb[:, :, 2]

        ret, threshold = cv2.threshold(channel, 160, 255, cv2.THRESH_BINARY)

        result = img.copy()
        contours, hierarchy = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
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
            cv2.line(result, minX, minY, [0, 255, 0], 10)
            cv2.line(result, minY, maxX, [0, 255, 0], 10)
            cv2.line(result, maxX, maxY, [0, 255, 0], 10)
            cv2.line(result, maxY, minX, [0, 255, 0], 10)
            # print(f"{minX}, {minY}, {maxX}, {maxY}")
            return minX, minY, maxX, maxY
