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
            self.frame_width = self.cam.image_width_pixels
            self.frame_height = self.cam.image_height_pixels
            print(f"Image dimensions: {self.frame_width}x{self.frame_height}")
            self.cam.exposure_time_us = 10
            self.cam.frames_per_trigger_zero_for_unlimited = 0
            self.cam.image_poll_timeout_ms = 1000
            
            # Arm camera with 2 frame buffers
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
            
            start_time = time.time()
            self.frame_count = 0
            self.fps_update_time = start_time
            self.start_time = start_time
            self.fps_display = 0
            self.is_active = True
            
            print(f"ThorLabs camera {self.camera_id} initialized successfully")
            
        except Exception as e:
            print(f"Error initializing ThorLabs camera {self.camera_id}: {e}")
            self.cleanup()
            raise

    def read_frame(self):
        if self.cam is None or not self.is_active:
            return False, None
        
        if self.mono_to_color_processor is None:
            return False, None
            
        try:
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
            display_image = color_image.copy()
            cv2.putText(display_image, f"FPS: {self.fps_display:.1f}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_image, f"Frame: {self.frame_count}", (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            return True, display_image
        except Exception as e:
            self.is_active = False
            return False, None

    def get_black_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

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