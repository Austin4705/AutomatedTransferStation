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

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
import numpy as np

# Use context managers for automatic cleanup
with TLCameraSDK() as sdk:
    serials = sdk.discover_available_cameras()
    print("Found cameras:", serials)
    if not serials:
        raise SystemExit("No Thorlabs cameras detected")

    with sdk.open_camera(serials[0]) as cam:
        print("Model:", cam.model, "SN:", cam.serial_number)
        
        # Configure camera settings
        cam.exposure_time_us = 10000
        cam.frames_per_trigger_zero_for_unlimited = 0  # continuous mode
        cam.image_poll_timeout_ms = 1000  # 1 second timeout
        
        # Arm the camera with 2 frame buffers
        cam.arm(2)
        
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
            
            # Normalize the image to 8-bit for display/saving
            if img.dtype == np.uint16 or cam.bit_depth > 8:
                # Scale from 12/16-bit to 8-bit
                img_normalized = ((img - img.min()) / (img.max() - img.min()) * 255).astype(np.uint8)
            else:
                img_normalized = img
            
            cv2.imwrite("frame.png", img_normalized)
            print("Image saved as frame.png")
            
            # Make a deep copy if you need to keep the data
            # img_copy = np.copy(frame.image_buffer)
        else:
            print("Timeout: No frame received")
        
        # Disarm the camera
        cam.disarm()

print("Program completed successfully")