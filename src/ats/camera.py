import cv2
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import numpy as np
import threading
import time
import weakref

from .logger import Logger
from .algorithms import pipeline as algo_pipeline
from .algorithms.registry import get_active as algo_get_active
from .socket_manager import Socket_Manager
from .image_container import Image_Container
from .transfer_station import Transfer_Station


class Camera(ABC):
    """
    Abstract base class for camera hardware.

    Subclasses MUST implement ``initialize_camera``, ``read_frame``,
    ``get_black_frame``, and ``cleanup``.

    To register a new camera driver::

        @Camera.register("my_camera")
        class MyCamera(Camera):
            ...
    """

    # --------------- driver registry ---------------
    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """Class decorator that registers a Camera subclass under *name*."""
        def decorator(subclass):
            cls._registry[name] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, camera_id: int, camera_type: str = "usb"):
        """Factory: create a Camera by its registered driver name."""
        driver_cls = cls._registry.get(camera_type)
        if driver_cls is None:
            raise ValueError(
                f"Unknown camera type: '{camera_type}'. "
                f"Registered types: {list(cls._registry.keys())}"
            )
        return driver_cls(camera_id)

    # --------------- class-level state (TODO: move to Runtime) ---------------
    image_container: Image_Container = None
    global_list: dict = {}
    _lock = threading.Lock()
    _instances = weakref.WeakSet()

    @staticmethod
    def initialize_all_cameras(image_container: Image_Container, camera_type: str = "usb"):
        """Detect and initialise all available cameras of the given type, in parallel."""
        Camera.image_container = image_container
        max_cameras_to_check = int(os.getenv('MAX_CAMERAS', '3'))
        Camera.cleanup_all()
        Camera.global_list.clear()

        print(f"Searching for cameras (parallel, n={max_cameras_to_check})...")

        def _try_init(i):
            try:
                cam = Camera.create(camera_id=i, camera_type=camera_type)
                return i, cam, None
            except Exception as e:
                return i, None, e

        available_cameras = []
        with ThreadPoolExecutor(max_workers=max_cameras_to_check) as pool:
            futures = [pool.submit(_try_init, i) for i in range(max_cameras_to_check)]
            for fut in as_completed(futures):
                i, cam, err = fut.result()
                if err is not None:
                    print(f"Error checking camera {i}: {err}")
                    continue
                if cam is None or not cam.is_active:
                    print(f"Camera {i} failed to initialize")
                    continue
                print(f"Camera {i} successfully initialized")
                available_cameras.append(i)
                with Camera._lock:
                    Camera.global_list[i] = cam
                    Camera._instances.add(cam)

        if not available_cameras:
            print("No cameras detected on the system!")
        else:
            print(f"Detected {len(available_cameras)} cameras: {sorted(available_cameras)}")

    @staticmethod
    def cleanup_all():
        """Clean up all camera instances."""
        print(f"Cleaning up {len(Camera._instances)} camera instances")
        for camera in list(Camera._instances):
            try:
                camera.cleanup()
            except Exception:
                pass

    # --------------- instance lifecycle ---------------
    def __init__(self, camera_id: int):
        self.is_active = False
        self.camera_id = camera_id
        self.frame_lock = threading.Lock()
        self.current_frame = self.get_black_frame()
        self.snapshot_image = self.get_black_frame()
        self.snapshot_image_flake_hunted = self.get_black_frame()
        self.capture_thread = None
        self.whitebalance_enabled = False
        self._first_frame_event = threading.Event()

        # FPS tracking (protected by _fps_lock)
        self._fps_lock = threading.Lock()
        self.start_time = time.time()
        self.frame_count = 0
        self.last_fps_frame_count = 0
        self.fps_update_time = self.start_time
        self.fps_display = 0.0
        self.fps_total = 0.0
        self.fps_counter_enabled = False

        self.initialize_camera()

        if self.is_active:
            self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.capture_thread.start()
            init_timeout = float(os.getenv('CAMERA_INIT_TIMEOUT', '3'))
            if not self._first_frame_event.wait(timeout=init_timeout):
                Logger.log(f"Camera {camera_id}: no frame within {init_timeout}s, continuing")

    def __del__(self):
        self.cleanup()

    # --------------- abstract interface ---------------
    @abstractmethod
    def initialize_camera(self) -> None:
        """Initialise the camera hardware. Must set ``self.is_active``."""
        ...

    @abstractmethod
    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Return ``(success, frame_bgr)``."""
        ...

    @abstractmethod
    def get_black_frame(self) -> np.ndarray:
        """Return a black frame of the expected dimensions."""
        ...

    def set_exposure_time(self, exposure_time_us: int):
        """Override in subclasses that support exposure control."""
        Logger.log(f"set_exposure_time not implemented for camera {self.camera_id}")

    def cleanup(self):
        """Release resources. Subclasses should call ``super().cleanup()``."""
        self.is_active = False
        if self.capture_thread is not None and self.capture_thread.is_alive():
            try:
                self.capture_thread.join(timeout=1.0)
            except Exception as e:
                print(f"Error joining capture thread for camera {self.camera_id}: {e}")

    # --------------- frame capture loop ---------------
    def _capture_frames(self):
        """Background thread: continuously capture frames."""
        while self.is_active:
            try:
                ret, frame = self.read_frame()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                with self.frame_lock:
                    self.current_frame = frame
                if not self._first_frame_event.is_set():
                    self._first_frame_event.set()

                with self._fps_lock:
                    self.frame_count += 1
                    current_time = time.time()
                    if current_time - self.fps_update_time >= 3.0:
                        elapsed = current_time - self.fps_update_time
                        frames_since = self.frame_count - self.last_fps_frame_count
                        self.fps_display = frames_since / elapsed
                        self.fps_total = self.frame_count / (current_time - self.start_time)
                        self.last_fps_frame_count = self.frame_count
                        self.fps_update_time = current_time

            except Exception as e:
                print(f"Error in capture thread for camera {self.camera_id}: {e}")
                time.sleep(0.1)

    def get_frame(self) -> np.ndarray:
        """Get the most recent frame (thread-safe)."""
        with self.frame_lock:
            return self.current_frame.copy()

    # --------------- snapshots ---------------
    def snap_image(self):
        """Take a snapshot and store it."""
        frame = self.get_frame().copy()
        if self.whitebalance_enabled:
            frame = algo_pipeline.apply_pipeline("snapshot", frame)
        self.snapshot_image = frame
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT", "camera": self.camera_id})
        try:
            image_id = Camera.image_container.save_snapshot(Camera.image_container.active_chip_id, self.snapshot_image)
            image_metadata = {"key_value_pairs": {
                "x": Transfer_Station.subclass_instances.posX(),
                "y": Transfer_Station.subclass_instances.posY(),
            }}
            self.image_container.apply_metadata_to_image(image_id, image_metadata)
        except Exception as e:
            Logger.log_error(f"Error saving snapshot: {e}")
        return self.snapshot_image

    def snap_image_flake_hunted(self):
        """Take a flake-hunted snapshot and store it."""
        frame = self.get_frame()
        Socket_Manager.send_all_json({"type": "REFRESH_SNAPSHOT_FLAKE_HUNTED", "camera": self.camera_id})
        try:
            # self.snapshot_image_flake_hunted = CV_Functions.matGMM2DTransform(frame)
            self.snapshot_image_flake_hunted = frame
        except Exception as e:
            print(f"Error in flake hunting: {e}")
        try:
            Camera.image_container.save_flake_hunted_snapshot(Camera.image_container.active_chip_id, self.snapshot_image_flake_hunted)
        except Exception as e:
            Logger.log_error(f"Error saving flake hunted snapshot: {e}")
        return self.snapshot_image_flake_hunted

    # --------------- HTTP response helpers ---------------
    def get_single_frame_as_response(self):
        """Get a single frame formatted as an HTTP multipart response."""
        frame = self.get_frame()

        if self.whitebalance_enabled:
            frame = algo_pipeline.apply_pipeline("live_view", frame.copy())

        if self.fps_counter_enabled:
            with self._fps_lock:
                fps_display = self.fps_display
                fps_total = self.fps_total
                frame_count = self.frame_count
            cv2.putText(frame, f"FPS: {fps_display:.1f}, Total: {fps_total:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Frame: {frame_count}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Draw a crosshair in the middle of the frame
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            crosshair_length = 20
            color = (0, 0, 255)
            thickness = 2
            cv2.line(frame, (center_x - crosshair_length, center_y), (center_x + crosshair_length, center_y), color, thickness)
            cv2.line(frame, (center_x, center_y - crosshair_length), (center_x, center_y + crosshair_length), color, thickness)
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
        """Get the snapshot as an HTTP multipart response."""
        frame = self.snapshot_image
        # Display the *currently-active* focus metric so swaps are visible live.
        from .algorithms.focus_metric.color_features import color_ratio as _color_ratio
        focus_score = float(algo_get_active("focus_metric")(frame))
        color_ratio = float(_color_ratio(frame))
        cv2.putText(frame, f"Focus Score: {focus_score:.2f}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Color Ratio: {color_ratio:.2f}",
            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, png = cv2.imencode(".jpg", frame)
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )

    def get_flake_hunted_snapshot_as_response(self):
        """Get the flake-hunted snapshot as an HTTP multipart response."""
        frame = self.snapshot_image_flake_hunted
        ret, png = cv2.imencode(".jpg", frame)
        return (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + png.tobytes() + b"\r\n\r\n"
        )


# ──────────────────────────────────────────────────────────────
# Built-in Virtual camera (returns black frames, for dev/testing)
# ──────────────────────────────────────────────────────────────

@Camera.register("virtual")
class VirtualCamera(Camera):
    """A virtual camera that returns black frames. Useful for development."""

    def initialize_camera(self) -> None:
        print(f"[VirtualCam] Camera {self.camera_id} initialized (virtual)")
        self.is_active = True

    def read_frame(self) -> tuple[bool, np.ndarray]:
        return True, self.get_black_frame()

    def get_black_frame(self) -> np.ndarray:
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def cleanup(self):
        print(f"[VirtualCam] Camera {self.camera_id} cleaned up")
        super().cleanup()
