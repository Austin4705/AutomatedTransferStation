import cv2
from datetime import datetime
import os
import numpy as np
from cvFunctions import CVFunctions
import threading
import time
import weakref
from socket_manager import Socket_Manager

class Camera:
    global_list = dict() #Global list of camera class objects
    IMAGE_REPO_NAME = "images"
    
    # Class-level lock for thread safety
    _lock = threading.Lock()
    
    # Keep track of all camera instances for cleanup
    _instances = weakref.WeakSet()

    @staticmethod
    # Figures out how many cameras are connected to the system
    def initialize_all_cameras(sim_test=False):
        max_cameras_to_check = 4
        available_cameras = []
        
        # First, clean up any existing cameras
        Camera.cleanup_all()
        
        # Clear the global list
        Camera.global_list.clear()
        
        print("Searching for cameras...")
        for i in range(0, max_cameras_to_check):
            try:
                print(f"Trying camera {i}...")
                cap = cv2.VideoCapture(i)
                if not cap.isOpened():
                    print(f"  Camera {i} not opened with default backend, trying DSHOW...")
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        print(f"  Camera {i} not available")
                        continue
                
                # Try to read a test frame to verify the camera works
                ret, test_frame = cap.read()
                if not ret or test_frame is None:
                    print(f"  Camera {i} opened but could not read frame, skipping")
                    cap.release()
                    continue
                    
                print(f"  Camera {i} successfully initialized")
                available_cameras.append(i)
                
                # Create camera instance
                try:
                    camera = Camera(i, cap)
                    if camera.current_frame is None:
                        print(f"  Warning: Camera {i} initialized but no frame captured")
                except Exception as e:
                    print(f"  Error initializing camera {i}: {e}")
                    cap.release()
                    continue
            except Exception as e:
                print(f"Error checking camera {i}: {e}")

        if not available_cameras:
            print("No cameras detected on the system!")
            return {}
        else: 
            print(f"Detected {len(available_cameras)} cameras: {available_cameras}")
            return available_cameras
    
    @staticmethod
    def cleanup_all():
        """Clean up all camera instances"""
        print(f"Cleaning up {len(Camera._instances)} camera instances")
        for camera in list(Camera._instances):
            try:
                camera.cleanup()
            except:
                pass

    def __init__(self, cameraId, cap):
        self.video = cap
        self.is_active = True
        self.camera_id = cameraId
        self.frame_lock = threading.Lock()
        
        # Initialize frame buffers
        self.current_frame = None
        self.snapshot_image = None
        self.snapshot_image_flake_hunted = None
        
        # Start frame capture thread
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()
        
        # Wait for first frame
        timeout = 3.0  # seconds
        start_time = time.time()
        while self.current_frame is None:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                print(f"Warning: Timeout waiting for first frame from camera {cameraId}")
                break
        
        # Store in global list and instances set
        with Camera._lock:
            Camera.global_list[cameraId] = self
            Camera._instances.add(self)

    def __del__(self):
        """Clean up resources when the camera is deleted"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources explicitly"""
        if hasattr(self, 'is_active') and self.is_active:
            self.is_active = False
            
            # Wait for capture thread to terminate
            if hasattr(self, 'capture_thread') and self.capture_thread.is_alive():
                try:
                    self.capture_thread.join(timeout=1.0)
                except:
                    pass
                
            # Release video capture
            if hasattr(self, 'video') and self.video is not None:
                try:
                    self.video.release()
                    self.video = None
                except Exception as e:
                    print(f"Error releasing camera {self.camera_id}: {e}")
                    
            # Clear frame buffers
            self.current_frame = None
            self.snapshot_image = None
            self.snapshot_image_flake_hunted = None

    def _capture_frames(self):
        """Background thread to continuously capture frames"""
        last_error_time = 0
        error_count = 0
        
        while self.is_active:
            try:
                if not hasattr(self, 'video') or self.video is None or not self.video.isOpened():
                    time.sleep(0.1)
                    continue
                
                # Capture frame
                ret, frame = self.video.read()
                if not ret:
                    # Limit error logging to avoid flooding
                    current_time = time.time()
                    if current_time - last_error_time > 5.0:
                        print(f"Error: Could not read frame from camera {self.camera_id}")
                        last_error_time = current_time
                        error_count += 1
                        
                    # If we've had too many errors, sleep longer
                    if error_count > 10:
                        time.sleep(0.5)
                    else:
                        time.sleep(0.01)
                    continue
                
                # Reset error count on successful frame
                error_count = 0
                
                # Update current frame with thread safety
                with self.frame_lock:
                    self.current_frame = frame
                
                # Don't capture too fast
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in capture thread for camera {self.camera_id}: {e}")
                time.sleep(0.1)

    def get_frame(self):
        """Get the most recent frame (thread-safe)"""
        with self.frame_lock:
            if self.current_frame is None:
                return None
            return self.current_frame.copy()

    def get_single_frame_as_response(self):
        """Get a single frame formatted as an HTTP response"""
        frame = self.get_frame()
        if frame is None:
            return None
            
        try:
            ret, png = cv2.imencode(".jpg", frame)
            if not ret:
                return None
                
            return (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
            )
        except Exception as e:
            print(f"Error encoding frame: {e}")
            return None

    def save_image(self, frame):
        """Save an image to disk"""
        if frame is None:
            print("Cannot save None frame")
            return
            
        try:
            cv2.imwrite(
                f"../{Camera.IMAGE_REPO_NAME}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg",
                frame,
            )
        except Exception as e:
            print(f"Error saving image: {e}")

    def snap_image(self):
        """Take a snapshot and store it"""
        frame = self.get_frame()
        with self.frame_lock:
            self.snapshot_image = frame
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT", "camera": self.camera_id})
        return self.snapshot_image

    def snap_image_flake_hunted(self):
        """Take a flake hunted snapshot and store it"""
        frame = self.get_frame()
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT_FLAKE_HUNTED", "camera": self.camera_id})
        if frame is None:
            return None
            
        try:
            processed_frame = CVFunctions.matGMM2DTransform(frame)
            with self.frame_lock:
                self.snapshot_image_flake_hunted = processed_frame
            return self.snapshot_image_flake_hunted
        except Exception as e:
            print(f"Error in flake hunting: {e}")
            return None

    def get_snapshot_as_response(self):
        """Get the snapshot as an HTTP response"""
        # Take a new snapshot if needed
        if self.snapshot_image is None:
            self.snap_image()
            
        # Get the snapshot with thread safety
        with self.frame_lock:
            frame = self.snapshot_image
            
        if frame is None:
            # Return a blank image if we can't get a real one
            blank_image = np.zeros((480, 640, 3), np.uint8)
            ret, png = cv2.imencode(".jpg", blank_image)
        else:
            ret, png = cv2.imencode(".jpg", frame)
            
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    def get_flake_hunted_snapshot_as_response(self):
        """Get the flake hunted snapshot as an HTTP response"""
        # Take a new snapshot if needed
        if self.snapshot_image_flake_hunted is None:
            self.snap_image_flake_hunted()
            
        # Get the snapshot with thread safety
        with self.frame_lock:
            frame = self.snapshot_image_flake_hunted
            
        if frame is None:
            # Return a blank image if we can't get a real one
            blank_image = np.zeros((480, 640, 3), np.uint8)
            ret, png = cv2.imencode(".jpg", blank_image)
        else:
            ret, png = cv2.imencode(".jpg", frame)
            
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    @staticmethod
    def generate_video(camera):
        """Generate video frames with proper resource management"""
        try:
            while camera.is_active:
                frame = camera.get_frame()
                if frame is None:
                    # If we can't get a frame, pause briefly and try again
                    import time
                    time.sleep(0.1)
                    continue
                    
                # frame = Camera.matGMM2DTransform(frame)
                ret, png = cv2.imencode(".jpg", frame)
                if not ret:
                    continue
                    
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
                )
        except Exception as e:
            print(f"Error in generate_video for camera {camera.camera_id}: {e}")
        finally:
            # Ensure we don't leave any resources hanging
            pass

    @staticmethod
    def get_snapped_image_flake_hunted(camera):
        if not hasattr(camera, 'snapshot_image') or camera.snapshot_image is None:
            camera.snap_image()
            
        if not hasattr(camera, 'snapshot_image_flake_hunted') or camera.snapshot_image_flake_hunted is None:
            camera.snap_image_flake_hunted()
            
        if camera.snapshot_image_flake_hunted is None:
            # Return a blank image if we can't get a real one
            blank_image = np.zeros((480, 640, 3), np.uint8)
            ret, png = cv2.imencode(".jpg", blank_image)
        else:
            ret, png = cv2.imencode(".jpg", camera.snapshot_image_flake_hunted)
            
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    @staticmethod
    def get_snapped_image(camera):
        if not hasattr(camera, 'snapshot_image') or camera.snapshot_image is None:
            camera.snap_image()
            
        if camera.snapshot_image is None:
            # Return a blank image if we can't get a real one
            blank_image = np.zeros((480, 640, 3), np.uint8)
            ret, png = cv2.imencode(".jpg", blank_image)
        else:
            ret, png = cv2.imencode(".jpg", camera.snapshot_image)
            
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )