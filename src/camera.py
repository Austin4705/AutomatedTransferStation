import cv2
from datetime import datetime
import os
import numpy as np
from cvFunctions import CVFunctions

class Camera:
    global_list = dict() #Global list of camera class objects

    IMAGE_REPO_NAME = "images"

    @staticmethod
    # Figures out how many cameras are connected to the system
    def initialize_all_cameras(sim_test=False):
        max_cameras_to_check = 4
        available_cameras = []
        for i in range(0, max_cameras_to_check):
            cap = cv2.VideoCapture(i)
            if not cap.isOpened():
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    continue
            available_cameras.append(i)
            Camera.global_list[i] = Camera(i, cap)

        if not available_cameras:
            print("No cameras detected on the system!")
            return {}
        else: 
            print(f"Detected {len(available_cameras)} cameras: {available_cameras}")
            return available_cameras

    def __init__(self, cameraId, cap):
        self.video = cap

        #self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        #self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
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
            
        # print(f"Frame shape: {self.frame.shape if self.frame is not None else 'None'}")
        return self.frame

    def save_image(frame):
        cv2.imwrite(
            f"../{Camera.IMAGE_REPO_NAME}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg",
            frame,
        )

    def snap_image(self):
        self.snapshot_image = self.get_frame()
        return self.snapshot_image

    def snap_image_flake_hunted(self):
        frame = self.get_frame()
        self.snapshot_image_flake_hunted = CVFunctions.matGMM2DTransform(frame)
        return self.snapshot_image_flake_hunted

    @staticmethod
    def generate_video(camera):
        while True:
            # frame = Camera.matGMM2DTransform(frame)
            ret, png = cv2.imencode(".jpg", camera.get_frame())
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
            )

    @staticmethod
    def get_snapped_image_flake_hunted(camera):
        ret, png = cv2.imencode(".jpg", camera.snap_image_flake_hunted())
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )
