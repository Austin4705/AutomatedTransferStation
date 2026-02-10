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
from logger import Logger


@Camera.register("thor")
class Camera_Thor(Camera):

    def __init__(self, cameraId):
        self.sdk = None
        self.mono_to_color_sdk = None
        self.cam = None
        self.mono_to_color_processor = None
        super().__init__(cameraId)

    def initialize_camera(self):
        try:
            if self.camera_id > 0:
                print(f"Not trying any non-zero index")
                self.is_active = False
                self.cam = None
                return

            script_dir = os.path.dirname(os.path.abspath(__file__))
            dll_dir = os.path.join(script_dir, "thor_drivers")

            if not os.path.exists(dll_dir):
                raise FileNotFoundError(f"DLL directory not found: {dll_dir}")

            print(f"DLL directory: {dll_dir}")
            print(f"DLL directory exists: {os.path.exists(dll_dir)}")
            os.add_dll_directory(dll_dir)
            os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')

            self.sdk = TLCameraSDK()
            self.mono_to_color_sdk = MonoToColorProcessorSDK()
            serials = self.sdk.discover_available_cameras()
            if not serials:
                raise RuntimeError("No ThorLabs cameras found")
            
            self.cam = self.sdk.open_camera(serials[self.camera_id])
            print("Model:", self.cam.model, "SN:", self.cam.serial_number)
            print("Sensor type:", self.cam.camera_sensor_type)

            print(f"Max sensor dimensions: {self.cam.image_width_pixels}x{self.cam.image_height_pixels}")
            
            self.frame_width = self.cam.image_width_pixels
            self.frame_height = self.cam.image_height_pixels
            self.cam.exposure_time_us = int(os.getenv('CAMERA_EXPOSURE_TIME_US', '5000'))
            self.cam.image_poll_timeout_ms = 1000
            self.cam.frames_per_trigger_zero_for_unlimited = 0
            self.cam.arm(2)
            self.mono_to_color_processor = self.mono_to_color_sdk.create_mono_to_color_processor(
                self.cam.camera_sensor_type,
                self.cam.color_filter_array_phase,
                self.cam.get_color_correction_matrix(),
                self.cam.get_default_white_balance_matrix(),
                self.cam.bit_depth
            )
            self.mono_to_color_processor.color_space = COLOR_SPACE.SRGB
            self.mono_to_color_processor.output_format = FORMAT.BGR_PIXEL
            self.cam.issue_software_trigger()
            
            self.is_active = True
            print(f"ThorLabs camera {self.camera_id} initialized successfully, is-active: {self.is_active}, frame-width: {self.frame_width}, frame-height: {self.frame_height}")
            
        except Exception as e:
            print(f"Error initializing ThorLabs camera {self.camera_id}: {e}")
            self.cleanup()
            raise

    def read_frame(self):
        if self.cam is None or not self.is_active:
            return False, None
        
        if self.mono_to_color_processor is None:
            Logger.log("Mono to color processor is None")
            return False, None
            
        try:
            frame = self.cam.get_pending_frame_or_null()
            if frame is None:
                Logger.log("Frame is None. Try closing the program and waiting a few seconds before restarting.")
                return False, None
            
            img = frame.image_buffer
            color_image_flat = self.mono_to_color_processor.transform_to_24(
                img, self.frame_width, self.frame_height
            )
            color_image = color_image_flat.reshape(self.frame_height, self.frame_width, 3)

            height, width = color_image.shape[:2]
            color_image = cv2.resize(color_image, (int(width/2), int(height/2)), interpolation=cv2.INTER_AREA)

            return True, color_image
        except Exception as e:
            print(f"Error reading frame {self.camera_id}: {e}")
            self.is_active = False
            return False, None

    def get_black_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def set_exposure_time(self, exposure_time_us):
        self.cam.exposure_time_us = exposure_time_us

    def cleanup(self):
        """Clean up resources explicitly in the correct order"""
        super().cleanup()

        try:
            if self.mono_to_color_processor is not None:
                self.mono_to_color_processor.dispose()
                self.mono_to_color_processor = None
            if self.cam is not None:
                self.cam.disarm()
                self.cam.dispose()
                self.cam = None
            if self.mono_to_color_sdk is not None:
                self.mono_to_color_sdk.dispose()
                self.mono_to_color_sdk = None
            if self.sdk is not None:
                self.sdk.dispose()
                self.sdk = None
        except Exception as e:
            print(f"Error Cleaning up: {e}")
