import os
import sys
import cv2
import time

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

# Display settings
WINDOW_NAME = "ThorCam Live Feed"  # OpenCV window name

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
        
        # Configure camera settings
        cam.exposure_time_us = 10000  # 10ms exposure
        cam.frames_per_trigger_zero_for_unlimited = 0  # continuous mode
        cam.image_poll_timeout_ms = 1000  # 1 second timeout
        
        # Arm the camera with 2 frame buffers
        cam.arm(2)
        
        image_width = cam.image_width_pixels
        image_height = cam.image_height_pixels
        print(f"Image dimensions: {image_width}x{image_height}")
        
        # Set up the color processor
        print("Setting up color processor...")
        mono_to_color_processor = mono_to_color_sdk.create_mono_to_color_processor(
            cam.camera_sensor_type,
            cam.color_filter_array_phase,
            cam.get_color_correction_matrix(),
            cam.get_default_white_balance_matrix(),
            cam.bit_depth
        )
        mono_to_color_processor.color_space = COLOR_SPACE.SRGB
        mono_to_color_processor.output_format = FORMAT.BGR_PIXEL
        
        # Create OpenCV window for live display
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, 1280, 720)  # Set initial window size
        
        print(f"Live feed started. Press 'q' or ESC to quit.")
        
        # Start continuous acquisition
        cam.issue_software_trigger()
        
        # Live display loop
        start_time = time.time()
        frame_count = 0
        fps_update_time = start_time
        fps_display = 0
        
        try:
            while True:
                # Get a frame
                frame = cam.get_pending_frame_or_null()
                
                if frame is not None:
                    img = frame.image_buffer
                    
                    # Convert Bayer pattern to RGB
                    color_image_flat = mono_to_color_processor.transform_to_24(
                        img, image_width, image_height
                    )
                    color_image = color_image_flat.reshape(image_height, image_width, 3)
                    
                    frame_count += 1
                    
                    # Calculate FPS every second
                    current_time = time.time()
                    if current_time - fps_update_time >= 1.0:
                        elapsed = current_time - fps_update_time
                        fps_display = frame_count / (current_time - start_time)
                        fps_update_time = current_time
                    
                    # Add FPS overlay to the image
                    display_image = color_image.copy()
                    cv2.putText(display_image, f"FPS: {fps_display:.1f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(display_image, f"Frame: {frame_count}", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Display the frame
                    cv2.imshow(WINDOW_NAME, display_image)
                    
                    # Keep triggering for continuous acquisition
                    cam.issue_software_trigger()
                else:
                    # No frame available, wait a bit and trigger again
                    time.sleep(0.001)
                    cam.issue_software_trigger()
                
                # Check for key press (wait 1ms)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\nStopping live feed...")
                    break
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            # Clean up
            cam.disarm()
            mono_to_color_processor.dispose()
            cv2.destroyAllWindows()
            
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed if elapsed > 0 else 0
            print(f"\nSession complete!")
            print(f"Total frames: {frame_count}")
            print(f"Duration: {elapsed:.1f}s")
            print(f"Average FPS: {actual_fps:.1f}")

print("Program completed successfully")