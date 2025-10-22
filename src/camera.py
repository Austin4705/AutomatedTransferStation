import cv2
from datetime import datetime
import os
import numpy as np
import threading
import time
import weakref


from autofocus import Autofocus
from socket_manager import Socket_Manager
from image_container import Image_Container

# import transfer_functions
# from cv_functions import CV_Functions

class Camera:
    image_container: Image_Container = None
    global_list = dict()
    _lock = threading.Lock()
    _instances = weakref.WeakSet()

    @classmethod
    def create(cls, camera_id: int, camera_type: str = "usb"):
        """Factory method to create camera by type"""
        if camera_type == "usb":
            from cameras.camera_usb import Camera_USB
            return Camera_USB(camera_id)
        elif camera_type == "thor":
            from cameras.camera_thor import Camera_Thor
            return Camera_Thor(camera_id)
        else:
            return cls(camera_id)

    @staticmethod
    def initialize_all_cameras(image_container: Image_Container, type: str = "usb"):
        """Figures out how many cameras are connected to the system"""
        Camera.image_container = image_container
        max_cameras_to_check = 3
        available_cameras = []
        Camera.cleanup_all()
        Camera.global_list.clear()
        
        print("Searching for cameras...")
        for i in range(0, max_cameras_to_check):
            try:
                camera = Camera.create(camera_id=i, camera_type=type)

                if camera.is_active:
                    print(f"Camera {i} successfully initialized")
                    available_cameras.append(i)
                    with Camera._lock:
                        Camera.global_list[i] = camera
                        Camera._instances.add(camera)
                else:   
                    print(f"Camera {i} failed to initialize")
            except Exception as e:
                print(f"Error checking camera {i}: {e}")

        if not available_cameras:
            print("No cameras detected on the system!")
            return {}
        else: 
            print(f"Detected {len(available_cameras)} cameras: {available_cameras}")
    
    @staticmethod
    def cleanup_all():
        """Clean up all camera instances"""
        print(f"Cleaning up {len(Camera._instances)} camera instances")
        for camera in list(Camera._instances):
            try:
                camera.cleanup()
            except:
                pass

    def __init__(self, cameraId):
        self.is_active = False
        self.camera_id = cameraId
        self.frame_lock = threading.Lock()
        self.current_frame = self.get_black_frame()
        self.snapshot_image = self.get_black_frame()
        self.snapshot_image_flake_hunted = self.get_black_frame()
        self.capture_thread = None
        
        self.initialize_camera()

        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()
        time.sleep(os.getenv('CAMERA_INIT_TIMEOUT', 3))
        
    def __del__(self):
        """Clean up resources when the camera is deleted"""
        self.cleanup()

    def cleanup(self):
        self.is_active = False
        if self.capture_thread is not None:
            if self.capture_thread.is_alive():
                try:
                    self.capture_thread.join(timeout=1.0)
                except Exception as e:
                    print(f"Error joining capture thread for camera {self.camera_id}: {e}")

    def initialize_camera(self):
        print(f"Trying camera {self.camera_id}...")
        self.is_active = True
        pass

    def read_frame(self):
        return True, self.get_black_frame()

    def _capture_frames(self):
        """Background thread to continuously capture frames"""
        while True:
            try:
                ret, frame = self.read_frame()
                if not ret: 
                    continue
                with self.frame_lock:
                    self.current_frame = frame
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in capture thread for camera {self.camera_id}: {e}")
                time.sleep(0.1)

    def get_frame(self):
        """Get the most recent frame (thread-safe)"""
        with self.frame_lock:
            return self.current_frame.copy()

    def get_black_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def save_image(self, frame):
        """Save an image to disk"""
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
        self.snapshot_image = frame
        print(self.snapshot_image.shape)
        Camera.image_container.save_snapshot(Camera.image_container.active_chip_id, self.snapshot_image)
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT", "camera": self.camera_id})

    def snap_image_flake_hunted(self):
        """Take a flake hunted snapshot and store it"""
        frame = self.get_frame()
        try:
            # self.snapshot_image_flake_hunted = CV_Functions.matGMM2DTransform(frame)
            self.snapshot_image_flake_hunted = frame
        except Exception as e:
            print(f"Error in flake hunting: {e}")
        Camera.image_container.save_flake_hunted_snapshot(Camera.image_container.active_chip_id, self.snapshot_image_flake_hunted)
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT_FLAKE_HUNTED", "camera": self.camera_id})


    def get_single_frame_as_response(self):
        """Get a single frame formatted as an HTTP response"""
        frame = self.get_frame()
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

    def get_snapshot_as_response(self):
        """Get the snapshot as an HTTP response"""
        frame = self.snapshot_image
        focus_score = Autofocus.calculate_focus_score(frame)
        has_enough_edges = Autofocus.get_edge_count(frame)
        color_ratio = Autofocus.get_color_features(frame)
        cv2.putText(
            frame,
            f"Focus Score: {focus_score:.2f} {has_enough_edges}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),  # White text
            2  # Thickness
        )
        cv2.putText(
            frame,
            f"Color Ratio: {color_ratio:.2f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),  # White text
            2  # Thickness
        )
        ret, png = cv2.imencode(".jpg", frame)
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    def get_flake_hunted_snapshot_as_response(self):
        """Get the flake hunted snapshot as an HTTP response"""
        frame = self.snapshot_image_flake_hunted
        ret, png = cv2.imencode(".jpg", frame)
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )