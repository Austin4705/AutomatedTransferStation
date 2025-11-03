import math
from typing import Dict, Callable
import threading
import time
import os
import json


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

        pics_until_focus = int(data.get("pics_until_focus", 300))
        initial_wait_time = float(data.get("initial_wait_time", 8))
        focus_wait_time = float(data.get("focus_wait_time", 8))
        camera_index = int(data.get("camera_index", 0))
        save_images = data.get("save_images", True)

        for wafer in data.get("wafers", [{}]):
            wafer_id = wafer.get("id")
            start = wafer.get("start", {})
            start_x = float(start.get("x"))
            start_y = float(start.get("y"))
            end = wafer.get("end", {})
            end_x = float(end.get("x"))
            end_y = float(end.get("y"))

            x_steps = int(abs(end_x - start_x) / travel["x"])
            y_steps = int(abs(end_y - start_y) / travel["y"])
            Logger.log(f"Creating {x_steps+1}x{y_steps+1} = {(x_steps+1)*(y_steps+1)} photos")
            points = []
            going_right = True
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
            self.transfer_station.moveXY(start_x, start_y)
            self.transfer_station.wait(initial_wait_time)
            # self.transfer_station.autoFocus()

            counter = 1
            for x, y in points:
                while True:
                    if Transfer_Functions.execute:
                        break
                    time.sleep(0.01)
                    
                self.transfer_station.moveXY(x, y)
                if counter % pics_until_focus == 0:
                    # self.transfer_station.autoFocus(camera_index)
                    pass

                self.transfer_station.wait(wait_time)
                image = Camera.global_list[camera_index].get_frame()
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
        try:
            x = data.get("x")
            if x is None:
                Logger.log_error("moveX: Missing 'x' parameter")
                return
            Logger.log(f"Moving to X: {x}")
            self.transfer_station.moveX(x)
        except Exception as e:
            Logger.log_error(f"Error moving X: {str(e)}")

    @transfer_function("MOVEY")
    def move_y(self, data: dict):
        """Move to absolute Y position"""
        try:
            y = data.get("y")
            if y is None:
                Logger.log_error("moveY: Missing 'y' parameter")
                return
            Logger.log(f"Moving to Y: {y}")
            self.transfer_station.moveY(y)
        except Exception as e:
            Logger.log_error(f"Error moving Y: {str(e)}")

    @transfer_function("MOVEZ")
    def move_z(self, data: dict):
        """Move to absolute Z position"""
        try:
            z = data.get("z")
            if z is None:
                Logger.log_error("moveZ: Missing 'z' parameter")
                return
            Logger.log(f"Moving to Z: {z}")
            self.transfer_station.moveZ(z)
        except Exception as e:
            Logger.log_error(f"Error moving Z: {str(e)}")

    @transfer_function("MOVEXY")
    def move_xy(self, data: dict):
        """Move to absolute XY position"""
        try:
            x = data.get("x")
            y = data.get("y")
            if x is None or y is None:
                Logger.log_error("moveXY: Missing 'x' or 'y' parameter")
                return
            Logger.log(f"Moving to XY: ({x}, {y})")
            self.transfer_station.moveXY(x, y)
        except Exception as e:
            Logger.log_error(f"Error moving XY: {str(e)}")
