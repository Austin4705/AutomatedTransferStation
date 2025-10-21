import cv2
from datetime import datetime
import os
import numpy as np
import time

from camera import Camera


class Camera_USB(Camera):
    def initialize_camera(self):
        if os.name == 'nt':  # Check if running on Windows
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_id)
        while not self.cap.isOpened():
            time.sleep(0.1)
        self.is_active = True
        self.frame_height = os.getenv(f'CAMERA{self.camera_id}_RESOLUTION_HEIGHT', 480)
        self.frame_width = os.getenv(f'CAMERA{self.camera_id}_RESOLUTION_WIDTH', 640)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def read_frame(self):
        return self.cap.read()

    def __init__(self, cameraId):
        super().__init__(cameraId)

    def get_black_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def cleanup(self):
        """Clean up resources explicitly"""
        super().cleanup()

        if self.cap is not None:
            try:
                self.cap.release()
                self.cap = None
            except Exception as e:
                print(f"Error releasing camera {self.camera_id}: {e}")