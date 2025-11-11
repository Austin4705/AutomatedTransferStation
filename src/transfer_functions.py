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
from logger import Logger
from camera import Camera

transfer_functions_dict: Dict[str, Callable] = {}
def transfer_function(command: str):
    """Decorator to register packet handlers"""
    def decorator(func):
        transfer_functions_dict[command] = func
        return func
    return decorator

class Transfer_Functions:
    """Class containing all transfer functions"""
    executing_threads = dict()
    execute = True

    def __init__(self, transfer_station, image_container) -> None:
        self.transfer_station = transfer_station
        self.image_container = image_container
        pass
    
    def run_command(self, command: str, data: dict):
        """
        given a command and parameters, execute the command
        """
        thread = threading.Thread(target=self.execute_command, args=(command, data))
        thread.daemon = True
        thread.start()

    @transfer_function("EXECUTE_COMMAND")
    def execute_command(self, command: str, data: dict):
        result = transfer_functions_dict[command](self, data)
        if result is not None:
            Logger.log(f"Transfer Function executed: {command}")

    @transfer_function("SET_EXPOSURE_TIME")
    def set_exposure_time(self, data: dict):
        camera_index = int(data.get("camera_index", 0))
        exposure_time_us = int(data.get("exposure_time_us", 10000))
        Logger.log(f"Setting exposure time for camera {camera_index} to {exposure_time_us} us")
        Camera.global_list[camera_index].set_exposure_time(exposure_time_us)
        Logger.log(f"Exposure time set for camera {camera_index} to {exposure_time_us} us")

    @transfer_function("PAUSE_EXECUTION")
    def pause_execution(self):
        self.execute = False

    @transfer_function("RESUME_EXECUTION")
    def resume_execution(self):
        self.execute = True

    @transfer_function("CANCEL_EXECUTION")
    def cancel_execution(self):
        self.execute = False
        for thread in self.executing_threads:
            self.executing_threads[thread] = False
            Logger.log(f"Thread {thread} signaled to stop")

    @transfer_function("RUN_TRACE_OVER")
    def run_trace_over(self, data):
        """Execute trace over with the provided configuration"""
        Logger.log("Type of data: " + type(data).__name__)
        Logger.log("Data: " + str(data))
    # def temp(self, data):
        
        MAGNIFICATION_TRAVEL = self.transfer_station.MAGNIFICATION_TRAVEL
        magnification = int(data.get("magnification", 20))
        wait_time = MAGNIFICATION_TRAVEL[magnification].get("wait_time", 1)
        travel = MAGNIFICATION_TRAVEL[magnification]

        pics_until_focus = int(data.get("pics_until_focus", 10))
        initial_wait_time = float(data.get("initial_wait_time", 25))
        focus_wait_time = float(data.get("focus_wait_time", 8))
        camera_index = int(data.get("camera_index", 0))
        camera = Camera.global_list[camera_index]
        save_images = data.get("save_images", True)

        for wafer in data.get("wafers", [{}]):
            wafer_id = wafer.get("id")
            start = wafer.get("start", {})
            start_x = float(start.get("x"))
            start_y = float(start.get("y"))
            start_z = float(start.get("z"))
            end = wafer.get("end", {})
            end_x = float(end.get("x"))
            end_y = float(end.get("y"))

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
                    "pics_until_focus": pics_until_focus,
                    "initial_wait_time": initial_wait_time,
                    "focus_wait_time": focus_wait_time,
                    "camera_index": camera_index,
                    }
                })
            self.transfer_station.moveXY(start_x, start_y)
            self.transfer_station.wait(initial_wait_time)
            self.auto_focus(camera, self.transfer_station, n_samples_coarse= 80, z_range_coarse=1.5)

            counter = 1
            for x, y in points:
                Logger.log(f"Transfer Functions executing: {Transfer_Functions.execute}")
                while True:
                    if Transfer_Functions.execute:
                        break
                    time.sleep(0.01)
                    
                    
                self.transfer_station.moveXY(x, y)
                self.transfer_station.moveZ(start_z)
                if counter % pics_until_focus == 0:
                    self.auto_focus(camera, self.transfer_station)
                    pass

                self.transfer_station.wait(wait_time)
                image = camera.get_frame()
                if Autofocus.exist_color_features(image) and Autofocus.get_edge_count(image) < 10:
                    self.auto_focus(camera, self.transfer_station)
                    pass

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

    def auto_focus2(self, camera, transfer_station):
        original_z_pos = transfer_station.posZ()
        frame = camera.get_frame()
        original_edge_count = Autofocus.get_edge_count(frame),
        if not Autofocus.exist_color_features(frame):
            Logger.log("No color features exist")
            return
        z_range = 0.5
        def func():
            timestamp = time.time()
            while time.time() - timestamp < 2:
                Logger.log(f"Z: {transfer_station.posZ()}")
        transfer_station.moveZRel(-z_range/2)
        func()
        transfer_station.moveZRel(z_range)
        func()
        transfer_station.moveZRel(-z_range/2)
        func()

    def auto_focus(self, camera, transfer_station, n_samples_coarse=20, n_samples_fine=20, z_range_coarse=0.5, z_range_fine=0.1):
        Logger.log("Auto Focus")
    # def blank(self, data: dict):
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
                z_step = z_range / n_samples

                # timestamp_move = time.time()
                transfer_station.moveZRel(z_step)
                # Logger.log(f"Time to move: {time.time() - timestamp_move}")
                # time.sleep(0.1)

                edge_count = Autofocus.get_edge_count(camera.get_frame())
                z_pos = -z_range/2 + (i * z_step)
                edge_counts.append((edge_count, z_pos))
                total_edge.append((edge_count, z_pos))
                Logger.log(f"i: {i}, Z: {z_pos}, Edge Count: {edge_count}")

            best_focus = max(edge_counts, key=lambda x: x[0])
            Logger.log(f"Best focus i: {i}, Z: {best_focus[1]}, Edge count: {best_focus[0]}")
            if(best_focus[0] == 0):
                Logger.log("Best focus is at 0")
                return -z_range/2
            else:
                return -z_range/2+best_focus[1]

        if(original_edge_count == 0):
            Logger.log(f"Original edge count is at ({original_edge_count})")
            best_focus = scan_z_range(original_z_pos, z_range_coarse, n_samples_coarse)
            transfer_station.moveZRel(best_focus)
        else:
            Logger.log(f"Original edge count is greater than 0 ({original_edge_count})")


        scan_z_range(original_z_pos, z_range_fine, n_samples_fine)

        def fit_gaussian(edges):
            edge_val_np = np.array([pt[0] for pt in edges])
            z_val_np = np.array([pt[1] for pt in edges])

            if max(edge_val_np, default=0) == 0:
                Logger.log("All edge counts in total_edge are 0")
                return

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
                    return popt[1]
                else:
                    return 0
            except Exception as e:
                Logger.log_error(f"Error fitting Gaussian: {e}")
                return 0
        best_focus = fit_gaussian(total_edge)
        offset = -z_range_fine/2+1*z_range_fine/n_samples_fine
        transfer_station.moveZRel(best_focus+offset)
        print(total_edge)

    #Takes Seconds
    def time_stamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]     
    
    def send_command(self, command):
        response = self._send_command(command)
        if(response is not None):
            self.add_response(response) 
        self.send_command_history.append({
            'timestamp': Transfer_Functions.time_stamp(),
            'command': command,
            'response': response
        })
        return response
    
    @transfer_function("TEST_COMMAND")
    def test_command(self, data: dict):
        Logger.log("Test Command")
        Logger.log(data)
