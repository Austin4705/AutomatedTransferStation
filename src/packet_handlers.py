from typing import Any, Dict, Callable
import json
import ast
import threading
from threading import Thread

import camera
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
            print(f"Executing transfer function: {data}, {packet_type}")
            if "transfer_function_name" not in data or transfer_function_name not in transfer_functions_dict:
                Socket_Manager.send_error("Missing or invalid transfer function name")
                return
            
            transfer_function_name = data["transfer_function_name"].strip()
            transfer_function = transfer_functions_dict[transfer_function_name]

            parameters_str = "[]"
            if "parameters" in data:
                parameters_str = data["parameters"].strip()
                if not parameters_str.startswith('{') and not parameters_str.endswith('}'):
                    parameters_str = '[' + parameters_str + ']'
                try:
                    parameters = json.loads(parameters_str)
                except json.JSONDecodeError:
                    parameters = ast.literal_eval(parameters_str)
                if not isinstance(parameters, list):
                    parameters = [parameters]

        except Exception as e:
            Socket_Manager.send_error(f"Parameter parsing error: {str(e)}")
            return
        PacketHandlers.transfer_functions.run_command(transfer_function, parameters)

    @packet_handler("REQUEST_STATE")
    def handle_request_state(packet_type: str, data: dict):
        message = {
            "type": "STATE",
            "state": {
                "position": {
                    "x": PacketHandlers.transfer_station.posX(),
                    "y": PacketHandlers.transfer_station.posY()
                }
            }
        }
        # Logger.log(f"Sending state: {message}")
        Socket_Manager.send_all_json(message)

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
        PacketHandlers.transfer_functions.stop_execution()
        Logger.log("All operations cancelled")

    @packet_handler("SNAP_SHOT")
    def handle_snap_shot(packet_type: str, data: dict):
        camera.Camera.global_list[data["camera"]].snap_image()
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT",
            "camera": data["camera"]
        })

    @packet_handler("SNAP_SHOT_FLAKE_HUNTED")
    def handle_snap_shot_flake_hunted(packet_type: str, data: dict):
        camera.Camera.global_list[data["camera"]].snap_image_flake_hunted()
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT_FLAKE_HUNTED",
            "camera": data["camera"]
        })

    @packet_handler("REQUEST_LOG_MESSAGES")
    def handle_request_log_messages(packet_type: str, data: dict):
        messages = self.logger.get_messages(50)
        Socket_Manager.send_all_json({
            "type": "RESPONSE_LOG_MESSAGES",
            "messages": messages
        })

    

        