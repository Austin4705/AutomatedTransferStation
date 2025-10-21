import threading
import os
import sys
import time
import weakref
import cv2
import numpy as np

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, SENSOR_TYPE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_mono_to_color_enums import COLOR_SPACE
from thorlabs_tsi_sdk.tl_color_enums import FORMAT

from camera import Camera

class Camera_Thor(Camera):

    def __init__(self, cameraId, cap):
        super().__init__(cameraId, cap)

    def initialize_camera(self):

        script_dir = os.path.dirname(os.path.abspath(__file__))
        dll_dir = os.path.join(script_dir, "thor_drivers")

        if not os.path.exists(dll_dir):
            raise FileNotFoundError(f"DLL directory not found: {dll_dir}")
        print(f"DLL directory: {dll_dir}")
        print(f"DLL directory exists: {os.path.exists(dll_dir)}")
        os.add_dll_directory(dll_dir)
        os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')

        with TLCameraSDK() as sdk, MonoToColorProcessorSDK() as mono_to_color_sdk:
            serials = sdk.discover_available_cameras()
            with sdk.open_camera(serials[self.camera_id]) as cam:
                print("Model:", cam.model, "SN:", cam.serial_number)
                print("Sensor type:", cam.camera_sensor_type)
                cam.exposure_time_us = 10000
                cam.frames_per_trigger_zero_for_unlimited = 0
                cam.image_poll_timeout_ms = 1000
                cam.arm(2)
                self.frame_width = cam.image_width_pixels
                self.frame_height = cam.image_height_pixels
                print(f"Image dimensions: {self.frame_width}x{self.frame_height}")

                self.mono_to_color_processor = mono_to_color_sdk.create_mono_to_color_processor(
                    cam.camera_sensor_type,
                    cam.color_filter_array_phase,
                    cam.get_color_correction_matrix(),
                    cam.get_default_white_balance_matrix(),
                    cam.bit_depth
                )
                self.mono_to_color_processor.color_space = COLOR_SPACE.SRGB
                self.mono_to_color_processor.output_format = FORMAT.BGR_PIXEL
                cam.issue_software_trigger()        
                start_time = time.time()
                self.frame_count = 0
                self.fps_update_time = start_time
                self.fps_display = 0
                self.is_active = True
                self.cam = cam

    def read_frame(self):
        frame = self.cam.get_pending_frame_or_null()
        if frame is None:
            return False, None
        img = frame.image_buffer
        color_image_flat = self.mono_to_color_processor.transform_to_24(
            img, self.frame_width, self.frame_height
        )
        color_image = color_image_flat.reshape(self.frame_height, self.frame_width, 3)

        self.frame_count += 1
        current_time = time.time()
        if current_time - self.fps_update_time >= 1.0:
            elapsed = current_time - self.fps_update_time
            self.fps_display = self.frame_count / (current_time - self.start_time)
            self.fps_update_time = current_time
        display_image = color_image
        cv2.putText(display_image, f"FPS: {self.fps_display:.1f}", (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_image, f"Frame: {self.frame_count}", (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return True, display_image

    def __init__(self, cameraId):
        super().__init__(cameraId)

    def get_black_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def cleanup(self):
        """Clean up resources explicitly"""
        super().cleanup()

        if self.cam is not None:
            try:
                self.cam.disarm()
                self.cam = None
            except Exception as e:
                print(f"Error releasing camera {self.camera_id}: {e}")
