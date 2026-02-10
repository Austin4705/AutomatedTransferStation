from typing import Any, Dict, Callable
import json
import ast
import threading
from threading import Thread

from camera import Camera
from transfer_functions import transfer_functions_dict, Transfer_Functions
from image_container import Image_Container
from transfer_station import Transfer_Station 
from socket_manager import Socket_Manager
from logger import Logger

_handlers: Dict[str, Callable] = {}
def packet_handler(packet_type: str):
    """Decorator to register packet handlers"""
    def decorator(func):
        # If the function is already a classmethod, get its __func__ attribute
        if isinstance(func, classmethod):
            func = func.__func__
        _handlers[packet_type] = func
        return classmethod(func)
    return decorator

class PacketHandlers:
    """Class containing all packet handlers"""
    transfer_station = None

    def __init__(self, transfer_station: Transfer_Station, image_container: Image_Container):
        print(f"Initializing PacketHandlers")
        PacketHandlers.transfer_station = transfer_station
        PacketHandlers.image_container = image_container
        PacketHandlers.transfer_functions = Transfer_Functions(transfer_station, image_container)
        self.packet_handlers = _handlers
    
    @packet_handler("ACK")
    def handle_ack(packet_type: str, data: dict):
        print("ACK received")
        Socket_Manager.send_all_json({ "type": "ACK", })

    @packet_handler("SEND_COMMAND")
    def handle_send_command(packet_type: str, data: dict):
        command = data["command"]
        print(f"Executing command: {command}")
        PacketHandlers.transfer_station.send_command(command)

    @packet_handler("EXECUTE_TRANSFER_FUNCTION")
    def handle_execute_transfer_function(packet_type: str, data: dict):
        try:
            Logger.log(f"Executing transfer function: {data}, {packet_type}")
            transfer_function_name = data["transfer_function_name"]
            parameters = json.loads(data["parameters"])[0]
            PacketHandlers.transfer_functions.run_command(transfer_function_name, parameters)
        except Exception as e:
            Logger.log_error(f"Error executing transfer function: {str(e)}")
            return

    @packet_handler("REQUEST_STATE")
    def handle_request_state(packet_type: str, data: dict):
        message = {
            "type": "STATE",
            "state": {
                "position": {
                    "x": PacketHandlers.transfer_station.posX(),
                    "y": PacketHandlers.transfer_station.posY(),
                    "z": PacketHandlers.transfer_station.posZ(),
                }
            }
        }
        # Logger.log(f"Sending state: {message}")
        Socket_Manager.send_all_json(message)

    @packet_handler("TOGGLE_WHITEBALANCE")
    def handle_toggle_whitebalance(packet_type: str, data: dict):
        Logger.log(f"TOGGLE_WHITEBALANCE received data: {data}")
        state = data.get("state", "off").lower()
        camera_index = int(data.get("camera_index", 0))
        Logger.log(f"Camera index: {camera_index}, State: {state}, Available cameras: {list(Camera.global_list.keys())}")

        if camera_index not in Camera.global_list:
            Logger.log_error(f"Camera {camera_index} not found in global list")
            return

        camera = Camera.global_list[camera_index]
        camera.whitebalance_enabled = (state == "on")
        Logger.log(f"Whitebalance set to {camera.whitebalance_enabled} for camera {camera_index}")

    @packet_handler("TOGGLE_FPS_COUNTER")
    def handle_toggle_fps_counter(packet_type: str, data: dict):
        Logger.log(f"TOGGLE_FPS_COUNTER received data: {data}")
        state = data.get("state", "off").lower()
        camera_index = int(data.get("camera_index", 0))
        Logger.log(f"Camera index: {camera_index}, State: {state}, Available cameras: {list(Camera.global_list.keys())}")

        if camera_index not in Camera.global_list:
            Logger.log_error(f"Camera {camera_index} not found in global list")
            return

        camera = Camera.global_list[camera_index]
        camera.fps_counter_enabled = (state == "on")
        Logger.log(f"FPS counter set to {camera.fps_counter_enabled} for camera {camera_index}")

    @packet_handler("PAUSE_EXECUTION")
    def handle_pause_execution(packet_type: str, data: dict):
        PacketHandlers.transfer_functions.pause_execution()
        Logger.log("Execution paused")

    @packet_handler("RESUME_EXECUTION")
    def handle_resume_execution(packet_type: str, data: dict):
        PacketHandlers.transfer_functions.resume_execution()
        Logger.log("Execution resumed")

    @packet_handler("CANCEL_EXECUTION")
    def handle_cancel_execution(packet_type: str, data: dict):
        PacketHandlers.transfer_functions.cancel_execution()
        Logger.log("All operations cancelled")

    @packet_handler("SNAP_SHOT")
    def handle_snap_shot(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image()
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT",
            "camera": data["camera"]
        })

    @packet_handler("SNAP_SHOT_FLAKE_HUNTED")
    def handle_snap_shot_flake_hunted(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image_flake_hunted()
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT_FLAKE_HUNTED",
            "camera": data["camera"]
        })

    @packet_handler("REQUEST_LOG_MESSAGES")
    def handle_request_log_messages(packet_type: str, data: dict):
        messages = Logger.get_messages(50)
        Socket_Manager.send_all_json({
            "type": "RESPONSE_LOG_MESSAGES",
            "messages": messages
        })

    @packet_handler("SCAN_FLAKES")
    def handle_scan_flakes(packet_type: str, data: dict):
        try:
            # Logger.log(f"SCAN_FLAKES received data: {data}")
            parameters = json.loads(data["parameters"])
            PacketHandlers.transfer_functions.run_command("RUN_SCAN_FLAKES", parameters)
        except Exception as e:
            Logger.log_error(f"Error executing SCAN_FLAKES: {str(e)}")
            Socket_Manager.send_all_json({
                "type": "SCAN_FLAKES_RESULT",
                "success": False,
                "message": f"Error: {str(e)}"
            })

    @packet_handler("GOTO_FLAKE")
    def handle_goto_flake(packet_type: str, data: dict):
        try:
            # Logger.log(f"GOTO_FLAKE received data: {data}")
            image_id = data["image_id"]
            new_start_x = float(data["new_start_x"])
            new_start_y = float(data["new_start_y"])

            parameters = {
                "image_id": image_id,
                "new_start_x": new_start_x,
                "new_start_y": new_start_y
            }

            PacketHandlers.transfer_functions.run_command("RUN_GOTO_FLAKE", parameters)
        except Exception as e:
            Logger.log_error(f"Error executing GOTO_FLAKE: {str(e)}")
            Socket_Manager.send_all_json({
                "type": "GOTO_FLAKE_RESULT",
                "success": False,
                "message": f"Error: {str(e)}"
            })



