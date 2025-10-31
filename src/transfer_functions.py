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

    def execute_command(self, command: str, data: dict):
        result = transfer_functions_dict[command](self, data)
        if result is not None:
            Logger.log(f"Transfer Function executed: {command}")

    def pause_execution(self):
        self.execute = False

    def resume_execution(self):
        self.execute = True

    def stop_execution(self):
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


            # Calculate number of steps in each direction
            x_steps = int(abs(end_x - start_x) / travel["x"])
            y_steps = int(abs(end_y - start_y) / travel["y"])

            Logger.log(f"Creating {x_steps+1}x{y_steps+1} = {(x_steps+1)*(y_steps+1)} photos")
        
            # Generate snake-like pattern coordinates
            points = []
            going_right = True
            current_x = start_x

            for y in range(y_steps + 1):
                row_y = start_y + (y * travel["y"])
                sign = 1 if end_y >= start_y else -1
                row_y = start_y + (y * travel["y"] * sign)
                points.append((current_x, row_y))
            
                # Generate points for this row
                for x in range(1, x_steps + 1):
                    if going_right:
                        next_x = current_x - travel["x"]
                    else:
                        next_x = current_x + travel["x"]
                    points.append((next_x, row_y))
                    current_x = next_x
            
                # Change direction for next row
                going_right = not going_right
        
            # Generate commands from points
            counter = 1
            # wafer_id = self.image_container.new_wafer()
            self.transfer_station.moveXY(start_x, start_y)
            self.transfer_station.wait(initial_wait_time)
            # self.transfer_station.autoFocus()

            for x, y in points:
                self.transfer_station.moveXY(x, y)
                if counter % pics_until_focus == 0:
                    # self.transfer_station.autoFocus(camera_index)
                    pass

                self.transfer_station.wait(wait_time)
                image = Camera.global_list[camera_index].snap_image()
                # if save_images:
                #     image_metadata = {
                #         "wafer_id": wafer_id,
                #         "camera_index": camera_index,
                #         "x": x,
                #         "y": y,
                #         "sequence": counter,
                #         "timestamp": time.time(),
                #         "magnification": magnification,
                #     }
                #     self.image_container.add_image(image, wafer_id, image_metadata)
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
