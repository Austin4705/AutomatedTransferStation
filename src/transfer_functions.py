import math
from typing import Dict, Callable
import threading
import time
import os


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
    
    def run_command(self, command: str, params: list):
        """
        given a command and parameters, execute the command
        """
        thread = Thread(target=self.execute_command, args=(command, params))
        thread.daemon = True
        thread.start()

    def execute_command(self, command: str, params: list):
        if not params:
            result = _transfer_functions[command]()
        else:
            result = _transfer_functions[command](*params)
        if(result is not None):
            Logger.global_log(f"TS Command executed: {result}")
        else:
            Logger.global_log(f"TS Command executed")

    def pause_execution(self):
        self.execute = False

    def resume_execution(self):
        self.execute = True

    def stop_execution(self):
        self.execute = False
        for thread in self.executing_threads:
            self.executing_threads[thread] = False
            Logger.global_log(f"Thread {thread} signaled to stop")

    @transfer_function("run_trace_over")
    def run_trace_over(self, data):
        Logger.global_log("Serializing a script to run trace over")
        MAGNIFICATION_TRAVEL = self.transfer_station.MAGNIFICATION_TRAVEL
        
        # Extract parameters from data
        try:
            # Optional parameters with defaults
            magnification = int(data.get("magnification", 20))
            pics_until_focus = int(data.get("pics_until_focus", 300))
            pics_until_led = int(data.get("pics_until_led", 100))
            initial_wait_time = float(data.get("initial_wait_time", 8))
            focus_wait_time = float(data.get("focus_wait_time", 8))
            camera_index = int(data.get("camera_index", 0))
            wait_time = MAGNIFICATION_TRAVEL[magnification].get("wait_time", 1)
            save_images = data.get("save_images", True)

            # Get travel distances for current magnification
            travel = MAGNIFICATION_TRAVEL[magnification]
            #Wafer generation
            for wafer in data.get("wafers", [{}]):
                bottom_left = wafer.get("bottomLeft", {})
                bottom_x = float(bottom_left.get("x"))
                bottom_y = float(bottom_left.get("y"))
                top_right = wafer.get("topRight", {})
                top_x = float(top_right.get("x"))
                top_y = float(top_right.get("y"))
            
                # Validate magnification
                if magnification not in MAGNIFICATION_TRAVEL:
                    Logger.log_error(f"Invalid magnification: {magnification}. Must be one of: {', '.join(map(str, MAGNIFICATION_TRAVEL.keys()))}")
            
                # Calculate number of steps in each direction
                x_steps = int(abs(top_x - bottom_x) / travel["x"])
                y_steps = int(abs(top_y - bottom_y) / travel["y"])

                Logger.log(f"Generating {x_steps+1}x{y_steps+1} = {(x_steps+1)*(y_steps+1)} points")
            
                # Generate snake-like pattern coordinates
                points = []
                going_right = True
                current_x = bottom_x
            
                for y in range(y_steps + 1):
                    row_y = bottom_y + (y * travel["y"])
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
                wafer_id = self.image_container.new_wafer()
                self.transfer_station.moveXY(bottom_x, bottom_y)
                self.transfer_station.wait(initial_wait_time)
                self.transfer_station.autoFocus()

                # Visit each point in the pattern
                for x, y in points:
                    # Move to position
                    self.transfer_station.moveXY(x, y)
                    # Perform autofocus or led on if needed
                    if counter % pics_until_led == 0:
                        self.transfer_station.led_on()
                    if counter % pics_until_focus == 0:
                        self.transfer_station.autoFocus(camera_index)

                    # Take picture
                    self.transfer_station.wait(wait_time)
                    image = Camera.global_list[camera_index].snap_image()
                    if save_images:
                        image_metadata = {
                            "wafer_id": wafer_id,
                            "camera_index": camera_index,
                            "x": x,
                            "y": y,
                            "sequence": counter,
                            "timestamp": time.time(),
                            "magnification": magnification,
                        }
                        self.image_container.add_image(image, wafer_id, image_metadata)
                    counter += 1
        except Exception as e:
            Logger.log_error(f"Error generating script: {str(e)}")            
