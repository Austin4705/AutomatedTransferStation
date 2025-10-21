import os
import sys
import cv2

# Add the thor_drivers directory to the DLL search path
script_dir = os.path.dirname(os.path.abspath(__file__))
dll_dir = os.path.join(script_dir, "cameras", "thor_drivers")

# Verify the DLL directory exists
if not os.path.exists(dll_dir):
    raise FileNotFoundError(f"DLL directory not found: {dll_dir}")

print(f"DLL directory: {dll_dir}")
print(f"DLL directory exists: {os.path.exists(dll_dir)}")

# For Python 3.8+, use add_dll_directory AND add to PATH
if sys.version_info >= (3, 8):
    os.add_dll_directory(dll_dir)
# Also add to PATH for compatibility
os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, SENSOR_TYPE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
from thorlabs_tsi_sdk.tl_mono_to_color_enums import COLOR_SPACE
from thorlabs_tsi_sdk.tl_color_enums import FORMAT
import numpy as np

# Use context managers for automatic cleanup
with TLCameraSDK() as sdk, MonoToColorProcessorSDK() as mono_to_color_sdk:
    serials = sdk.discover_available_cameras()
    print("Found cameras:", serials)
    if not serials:
        raise SystemExit("No Thorlabs cameras detected")

    with sdk.open_camera(serials[0]) as cam:
        print("Model:", cam.model, "SN:", cam.serial_number)
        print("Sensor type:", cam.camera_sensor_type)
        
        
        cam.exposure_time_us = 10000
        cam.frames_per_trigger_zero_for_unlimited = 0  # continuous mode
        cam.image_poll_timeout_ms = 1000  # 1 second timeout
        
        # Arm the camera with 2 frame buffers
        cam.arm(2)
        
        image_width = cam.image_width_pixels
        image_height = cam.image_height_pixels
        
        # Trigger image acquisition
        cam.issue_software_trigger()
        
        # Poll for a frame
        frame = cam.get_pending_frame_or_null()
        if frame is not None:
            img = frame.image_buffer  # NumPy array interface
            print("Frame shape:", img.shape, "dtype:", img.dtype)
            print("Frame count:", frame.frame_count)
            print("Bit depth:", cam.bit_depth)
            print("Image min:", img.min(), "max:", img.max())
            
            cam.disarm()
            
            print("Converting Bayer pattern to RGB...")
            with mono_to_color_sdk.create_mono_to_color_processor(
                cam.camera_sensor_type,
                cam.color_filter_array_phase,
                cam.get_color_correction_matrix(),
                cam.get_default_white_balance_matrix(),
                cam.bit_depth
            ) as mono_to_color_processor:
                mono_to_color_processor.color_space = COLOR_SPACE.SRGB
                mono_to_color_processor.output_format = FORMAT.BGR_PIXEL
                color_image_flat = mono_to_color_processor.transform_to_24(
                    img, image_width, image_height
                )
                color_image = color_image_flat.reshape(image_height, image_width, 3)

                print("Color image shape:", color_image.shape)
                cv2.imwrite("frame.png", color_image)
                print("Color image saved as frame.png")
        else:
            print("Timeout: No frame received")
            cam.disarm()

print("Program completed successfully")