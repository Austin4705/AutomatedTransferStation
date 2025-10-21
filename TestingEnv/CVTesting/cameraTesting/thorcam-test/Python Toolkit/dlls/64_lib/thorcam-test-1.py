import os
import sys
import cv2

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
import numpy as np

# Add the current directory to the DLL search path
dll_dir = os.path.dirname(os.path.abspath(__file__))
os.add_dll_directory(dll_dir)


# Use context managers for automatic cleanup
with TLCameraSDK() as sdk:
    serials = sdk.discover_available_cameras()
    print("Found cameras:", serials)
    if not serials:
        raise SystemExit("No Thorlabs cameras detected")

    with sdk.open_camera(serials[0]) as cam:
        print("Model:", cam.model, "SN:", cam.serial_number)
        
        cam.exposure_time_us = 10000
        cam.frames_per_trigger_zero_for_unlimited = 0  # continuous mode
        cam.image_poll_timeout_ms = 1000  # 1 second timeout
        
        # Arm the camera with 2 frame buffers
        cam.arm(2)
        cam.issue_software_trigger()
        
        frame = cam.get_pending_frame_or_null()
        if frame is not None:
            img = frame.image_buffer  # NumPy array interface
            print("Frame shape:", img.shape, "dtype:", img.dtype)
            print("Frame count:", frame.frame_count)
            print("Bit depth:", cam.bit_depth)
            print("Image min:", img.min(), "max:", img.max())
            
            if img.dtype == np.uint16 or cam.bit_depth > 8:
                img_normalized = ((img - img.min()) / (img.max() - img.min()) * 255).astype(np.uint8)
            else:
                img_normalized = img
            
            cv2.imwrite("frame.png", img_normalized)
            print("Image saved as frame.png")
        else:
            print("Timeout: No frame received")
        
        cam.disarm()

print("Program completed successfully")