import math
from typing import Dict, Callable
import threading
import time
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from autofocus import Autofocus
from image_container import Image_Container
from cv_functions import CV_Functions
from logger import Logger
from camera import Camera

transfer_functions_dict: Dict[str, Callable] = {}
def transfer_function(command: str):
    """Decorator to register transfer functions"""
    def decorator(func):
        transfer_functions_dict[command] = func
        return func
    return decorator

class Transfer_Functions:
    """Class containing all transfer functions.
    
    Uses threading.Event for pause/cancel so that waiting is efficient
    and thread-safe (no busy-loop on a bare bool).
    """

    def __init__(self, transfer_station, image_container) -> None:
        self.transfer_station = transfer_station
        self.image_container = image_container

        # Thread-safe execution control
        self._run_event = threading.Event()    # clear = paused, set = running
        self._cancel_event = threading.Event() # set = cancelled
        self._run_event.set()                  # start in "running" state

        self._active_threads: list[threading.Thread] = []
        self._threads_lock = threading.Lock()

    # --------------- execution control ---------------

    @property
    def is_executing(self) -> bool:
        """True when operations are allowed to proceed (not paused, not cancelled)."""
        return self._run_event.is_set() and not self._cancel_event.is_set()

    def wait_if_paused(self, timeout: float = 0.1) -> bool:
        """Block until un-paused, or return False immediately if cancelled."""
        while not self._cancel_event.is_set():
            if self._run_event.wait(timeout=timeout):
                return True   # running
        return False  # cancelled

    @transfer_function("PAUSE_EXECUTION")
    def pause_execution(self, *_args):
        self._run_event.clear()
        Logger.log("Execution paused")

    @transfer_function("RESUME_EXECUTION")
    def resume_execution(self, *_args):
        self._run_event.set()
        Logger.log("Execution resumed")

    @transfer_function("CANCEL_EXECUTION")
    def cancel_execution(self, *_args):
        self._cancel_event.set()
        self._run_event.set()  # unblock any waiting threads so they can check cancel
        Logger.log("All operations signalled to cancel")
        # Wait briefly for threads to finish
        with self._threads_lock:
            for t in self._active_threads:
                t.join(timeout=2.0)
            self._active_threads.clear()
        # Reset for next use
        self._cancel_event.clear()
        self._run_event.set()

    # --------------- command dispatch ---------------

    def run_command(self, command: str, data: dict):
        """Run a transfer function in a background thread."""
        thread = threading.Thread(target=self._execute_in_thread, args=(command, data), daemon=True)
        with self._threads_lock:
            self._active_threads.append(thread)
        thread.start()

    def _execute_in_thread(self, command: str, data: dict):
        try:
            self.execute_command(command, data)
        finally:
            with self._threads_lock:
                if threading.current_thread() in self._active_threads:
                    self._active_threads.remove(threading.current_thread())

    @transfer_function("EXECUTE_COMMAND")
    def execute_command(self, command: str, data: dict):
        handler = transfer_functions_dict.get(command)
        if handler is None:
            Logger.log_error(f"Unknown transfer function: {command}")
            return
        result = handler(self, data)
        if result is not None:
            Logger.log(f"Transfer Function executed: {command}")

    # --------------- transfer functions ---------------

    @transfer_function("SET_EXPOSURE_TIME")
    def set_exposure_time(self, data: dict):
        camera_index = int(data.get("camera_index", 0))
        exposure_time_us = int(data.get("exposure_time_us", 10000))
        Logger.log(f"Setting exposure time for camera {camera_index} to {exposure_time_us} us")
        Camera.global_list[camera_index].set_exposure_time(exposure_time_us)
        Logger.log(f"Exposure time set for camera {camera_index} to {exposure_time_us} us")

    @transfer_function("RUN_TRACE_OVER")
    def run_trace_over(self, data):
        Logger.log("Type of data: " + type(data).__name__)
        Logger.log("Data: " + str(data))
        
        MAGNIFICATION_TRAVEL = self.transfer_station.MAGNIFICATION_TRAVEL
        magnification = int(data.get("magnification", 20))
        wait_time = MAGNIFICATION_TRAVEL[magnification].get("wait_time", 1)
        travel = MAGNIFICATION_TRAVEL[magnification]

        initial_wait_time = float(data.get("initial_wait_time", 25))
        camera = Camera.global_list[int(data.get("camera_index", 0))]
        save_images = data.get("save_images", True)

        for wafer in data.get("wafers", [{}]):
            if self._cancel_event.is_set():
                Logger.log("Trace over cancelled")
                return

            wafer_id = wafer.get("id")
            start = wafer.get("start", {})
            start_x = float(start.get("x"))
            start_y = float(start.get("y"))
            start_z = float(start.get("z"))
            end = wafer.get("end", {})
            end_x = float(end.get("x"))
            end_y = float(end.get("y"))

            self.run_trace_over(start_x, end_x, start_y, end_y, start_z, travel, initial_wait_time, camera, save_images, wafer_id)

    @transfer_function("RUN_TRACE_OVER_AREA")
        Logger.log("Type of data: " + type(data).__name__)
        Logger.log("Data: " + str(data))
        
        MAGNIFICATION_TRAVEL = self.transfer_station.MAGNIFICATION_TRAVEL
        magnification = int(data.get("magnification", 20))
        wait_time = MAGNIFICATION_TRAVEL[magnification].get("wait_time", 1)
        travel = MAGNIFICATION_TRAVEL[magnification]

        initial_wait_time = float(data.get("initial_wait_time", 25))
        camera = Camera.global_list[int(data.get("camera_index", 0))]
        save_images = data.get("save_images", True)


        wafer_id = data.get("wafer_id")
        start_x = float(data.get("start_x", 0))
        start_y = float(data.get("start_y", 0))
        start_z = float(data.get("start_z", 0))
        end_x = float(data.get("end_x", 0))
        end_y = float(data.get("end_y", 0))

        self.run_trace_over(start_x, end_x, start_y, end_y, start_z, travel, initial_wait_time, camera, save_images, wafer_id) 


    @transfer_function("goto_wafer_image")
    def goto_wafer_image(self, data: dict):
        """Navigate to a specific wafer image location with optional offsets"""
        try:
            directory = data.get("directory")
            startXOffset = data.get("startXOffset", 0)
            startYOffset = data.get("startYOffset", 0)
            endXOffset = data.get("endXOffset", 0)
            endYOffset = data.get("endYOffset", 0)
            waferNumber = data.get("waferNumber")
            imageNumber = data.get("imageNumber")

            # Load image container for the specified directory
            image_container = Image_Container(self.transfer_station, directory)
            image_data = image_container.metadata.get("wafers")[waferNumber][imageNumber]
            x = image_data["x"]
            y = image_data["y"]

            Logger.log(f"Goto wafer {waferNumber} image {imageNumber} at {x}, {y}")
            Logger.log(f"Start Offset: ({startXOffset}, {startYOffset})")
            Logger.log(f"End Offset: ({endXOffset}, {endYOffset})")

            # Move to the image location with offset
            self.transfer_station.moveXY(x + startXOffset, y + startYOffset)
        except Exception as e:
            Logger.log_error(f"Error navigating to wafer image: {str(e)}")

    @transfer_function("MOVEX")
    def move_x(self, data: dict):
        """Move to absolute X position"""
        x = data.get("x")
        Logger.log(f"Moving to X: {x}")
        self.transfer_station.moveX(x)

    @transfer_function("MOVEY")
    def move_y(self, data: dict):
        """Move to absolute Y position"""
        y = data.get("y")
        Logger.log(f"Moving to Y: {y}")
        self.transfer_station.moveY(y)

    @transfer_function("MOVEZ")
    def move_z(self, data: dict):
        """Move to absolute Z position"""
        z = data.get("z")
        Logger.log(f"Moving to Z: {z}")
        self.transfer_station.moveZ(z)

    @transfer_function("MOVEXY")
    def move_xy(self, data: dict):
        """Move to absolute XY position"""
        x = data.get("x")
        y = data.get("y")
        Logger.log(f"Moving to XY: ({x}, {y})")
        self.transfer_station.moveXY(x, y)

    @transfer_function("MOVEXREL")
    def move_x_rel(self, data: dict):
        """Move relative X position"""
        x = data.get("x")
        Logger.log(f"Moving relative X: {x}")
        self.transfer_station.moveXRel(x)

    @transfer_function("MOVEYREL")
    def move_y_rel(self, data: dict):
        """Move relative Y position"""
        y = data.get("y")
        Logger.log(f"Moving relative Y: {y}")
        self.transfer_station.moveYRel(y)

    @transfer_function("MOVEZREL")
    def move_z_rel(self, data: dict):
        """Move relative Z position"""
        z = data.get("z")
        Logger.log(f"Moving relative Z: {z}")
        self.transfer_station.moveZRel(z)

    @transfer_function("MOVEXYREL")
    def move_xy_rel(self, data: dict):
        """Move relative XY position"""
        x = data.get("x")
        y = data.get("y")
        Logger.log(f"Moving relative XY: ({x}, {y})")
        self.transfer_station.moveXYRel(x, y)
    
    @transfer_function("AUTO_FOCUS")
    def auto_focus_caller(self, data: dict):
        camera_index = int(data.get("camera_index", 0))
        camera = Camera.global_list[camera_index]
        transfer_station = self.transfer_station
        self.auto_focus(camera, transfer_station)

    @transfer_function("TEST_COMMAND")
    def test_command(self, data: dict):
        Logger.log("Test Command")
        Logger.log(data)

    @transfer_function("RUN_SCAN_FLAKES")
    def run_scan_flakes(self, data: dict):
        """
        Scan flakes from multiple collections
        """
        try:
            from socket_manager import Socket_Manager

            Logger.log("Starting SCAN_FLAKES operation")
            collections = data.get("collections", [])

            if not collections:
                raise ValueError("No collections provided")

            for idx, collection_config in enumerate(collections):
                if self._cancel_event.is_set():
                    Logger.log("Scan flakes cancelled")
                    return

                collection_id = collection_config.get("collection_id")
                apply_whitebalance = collection_config.get("apply_whitebalance", False)
                wafer_type = collection_config.get("wafer_type", "HBn")

                Logger.log(f"Processing collection {idx + 1}/{len(collections)}")
                Logger.log(f"  Collection ID: {collection_id}")
                Logger.log(f"  Apply Whitebalance: {apply_whitebalance}")
                Logger.log(f"  Wafer Type: {wafer_type}")

            Socket_Manager.send_all_json({
                "type": "SCAN_FLAKES_RESULT",
                "success": True,
                "collectionCount": len(collections),
                "message": f"Successfully processed {len(collections)} collection(s)"
            })

        except Exception as e:
            from socket_manager import Socket_Manager
            Logger.log_error(f"Error in RUN_SCAN_FLAKES: {str(e)}")
            Socket_Manager.send_all_json({
                "type": "SCAN_FLAKES_RESULT",
                "success": False,
                "message": f"Error: {str(e)}"
            })

    @transfer_function("RUN_GOTO_FLAKE")
    def run_goto_flake(self, data: dict):
        """
        Navigate to a specific flake location based on image ID and new coordinates
        """
        try:
            image_id = data.get("image_id")
            new_start_x = float(data.get("new_start_x"))
            new_start_y = float(data.get("new_start_y"))

            if not image_id:
                raise ValueError("Image ID is required")

            Logger.log(f"Navigating to flake:")
            Logger.log(f"  Image ID: {image_id}")
            Logger.log(f"  New Start X: {new_start_x}")
            Logger.log(f"  New Start Y: {new_start_y}")

        except Exception as e:
            Logger.log_error(f"Error in RUN_GOTO_FLAKE: {str(e)}")

    def send_command(self, command):
        response = self._send_command(command)
        if(response is not None):
            self.add_response(response) 
        self._send_command_history.append({
            'timestamp': Transfer_Functions.time_stamp(),
            'command': command,
            'response': response
        })
        return response

    def run_trace_over(self, start_x, end_x, start_y, end_y, start_z, travel, initial_wait_time, camera, save_images, wafer_id):
        """Execute trace over with the provided configuration"""
            x_steps = int(abs(end_x - start_x) / travel["x"])
            y_steps = int(abs(end_y - start_y) / travel["y"])
            Logger.log(f"Creating {x_steps+1}x{y_steps+1} = {(x_steps+1)*(y_steps+1)} photos with {travel['x']}x {travel['y']}y travel per picture")
            points = []
            going_right = start_x >= end_x
            current_x = start_x
            for y in range(y_steps + 1):
                row_y = start_y + (y * travel["y"])
                sign = 1 if end_y >= start_y else -1
                row_y = start_y + (y * travel["y"] * sign)
                points.append((current_x, row_y))
            
                for x in range(1, x_steps + 1):
                    if going_right:
                        next_x = current_x - travel["x"]
                    else:
                        next_x = current_x + travel["x"]
                    points.append((next_x, row_y))
                    current_x = next_x
                going_right = not going_right
        
            if save_images:
                wafer_folder = self.image_container.load_or_create_chip_by_name(wafer_id)
                collection_id = self.image_container.create_new_collection(wafer_folder)
                self.image_container.apply_metadata_to_dataset(collection_id, {"key_value_pairs": 
                    {
                    "start_x": start_x,
                    "start_y": start_y,
                    "end_x": end_x,
                    "end_y": end_y,
                    "x_steps": x_steps,
                    "y_steps": y_steps,
                    "magnification": magnification,
                    "initial_wait_time": initial_wait_time,
                    }
                })
            self.transfer_station.moveXY(start_x, start_y)
            self.transfer_station.moveZ(start_z)
            self.transfer_station.wait(initial_wait_time)
            self.auto_focus(camera, self.transfer_station, n_samples_coarse= 80, z_range_coarse=1.5)

            came_before_no_background = False

            counter = 1
            for x, y in points:
                # Wait if paused, abort if cancelled
                if not self.wait_if_paused():
                    Logger.log("Trace over cancelled during execution")
                    return
                time.sleep(0.01)

                self.transfer_station.moveXY(x, y)
                self.transfer_station.wait(wait_time)
                image = camera.get_frame()
                is_background, bg_stats = CV_Functions.is_substrate_background(image)
                edge_count = Autofocus.get_edge_count(image)

                if is_background:
                    if edge_count < 10 or came_before_no_background:
                        Logger.log(f"Autofocusing - Substrate background: {is_background}, Edge count: {edge_count} - came before no background: {came_before_no_background} - pics until focus: {pics_until_focus}")
                        self.auto_focus(camera, self.transfer_station)
                    came_before_no_background = False
                else:
                    Logger.log("Skipping autofocus - not substrate background")
                    came_before_no_background = True

                if save_images:
                    image_id = self.image_container.upload_image(image, dataset_id=collection_id, image_name=f"image_{counter}")
                    image_metadata = {"key_value_pairs": {
                        "wafer_id": wafer_id,
                        "camera_index": camera_index,
                        "x": x,
                        "y": y,
                        "sequence": counter,
                        "timestamp": time.time(),
                        "magnification": magnification,
                    }}
                    self.image_container.apply_metadata_to_image(image_id, image_metadata)

                counter += 1

    def auto_focus(self, camera, transfer_station, n_samples_coarse=20, n_samples_fine=20, z_range_coarse=0.5, z_range_fine=0.1):
        Logger.log("Auto Focus")
        """Auto focus the camera at the current position"""

        original_z_pos = transfer_station.posZ()
        frame = camera.get_frame()

        if not Autofocus.exist_color_features(frame):
            Logger.log("No color features exist")

            return

        original_edge_count = Autofocus.get_edge_count(frame)

        total_edge = []

        def scan_z_range(center_z_pos, z_range, n_samples):
            edge_counts = []
            print(f"Moving from {center_z_pos} to Scanning Z range from {center_z_pos-z_range/2} to {center_z_pos+z_range/2}")
            transfer_station.moveZRel(-z_range/2)
            transfer_station.wait(1.25)
            for i in range(n_samples):
                if not self.wait_if_paused():
                    return 0.0  # cancelled

                z_step = z_range / n_samples

                transfer_station.moveZRel(z_step)

                edge_count = Autofocus.get_edge_count(camera.get_frame())
                z_pos = -z_range/2 + (i * z_step)
                edge_counts.append((edge_count, z_pos))
                total_edge.append((edge_count, z_pos))

            best_focus = max(edge_counts, key=lambda x: x[0])
            Logger.log(f"Best focus i: {i}, Z: {best_focus[1]}, Edge count: {best_focus[0]}")
            if(best_focus[0] == 0):
                Logger.log("Best focus is at 0")
                return -z_range/2
            else:
                return -z_range/2+best_focus[1]

        if(original_edge_count == 0):
            Logger.log(f"Original edge count is at ({original_edge_count})")
            best_focus_coarse = scan_z_range(original_z_pos, z_range_coarse, n_samples_coarse)
            transfer_station.moveZRel(best_focus_coarse)
        else:
            Logger.log(f"Original edge count is greater than 0 ({original_edge_count})")


        scan_z_range(original_z_pos, z_range_fine, n_samples_fine)

        def fit_gaussian(edges) -> float:
            edge_val_np = np.array([pt[0] for pt in edges])
            z_val_np = np.array([pt[1] for pt in edges])

            if max(edge_val_np, default=0) == 0:
                Logger.log("All edge counts in total_edge are 0")
                return 0.0

            def gaussian(x, amp, mean, std):
                return amp * np.exp(-((x - mean) ** 2) / (2 * std ** 2))

            try:
                popt, pcov = curve_fit(
                    gaussian, z_val_np,
                    edge_val_np,
                    p0=[edge_val_np.max(), z_val_np[np.argmax(edge_val_np)], 0.05]
                )
                Logger.log(f"Fitted parameters: amplitude={popt[0]:.2f}, mean={popt[1]:.5f}, std={popt[2]:.5f}")
                if popt[1] is not None:
                    return float(popt[1])
                else:
                    return 0.0
            except Exception as e:
                Logger.log_error(f"Error fitting Gaussian: {e}")
                return 0.0

        best_focus_fine = fit_gaussian(total_edge)
        offset = -z_range_fine/2+1*z_range_fine/n_samples_fine
        transfer_station.moveZRel(best_focus_fine+offset)
        print(total_edge)

    #Takes Seconds
    def time_stamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]     
    