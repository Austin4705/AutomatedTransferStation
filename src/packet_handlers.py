from typing import Any, Dict, Callable
import json
from socket_manager import Socket_Manager
from camera import Camera
from transfer_station import Transfer_Station 
import threading
from transfer_functions import TransferFunctions

# Dictionary to store packet handlers
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

    def __init__(self):
        print(f"Initializing PacketHandlers")
        Socket_Manager.packet_handlers = _handlers
    
    @packet_handler("SEND_COMMAND")
    def handle_send_command(packet_type: str, data: dict):
        command = data["command"]
        print(f"Executing command: {command}")
        PacketHandlers.transfer_station.send_command(command)

    @packet_handler("TS_COMMAND")
    def handle_ts_command(packet_type: str, data: dict):
        command = data["command"]
        parameters = data["parameters"]
        if hasattr(PacketHandlers.transfer_station, command):
            function = getattr(PacketHandlers.transfer_station, command)
            deserialized_parameters = json.loads(parameters) 
            result = function(*deserialized_parameters)
            PacketCommander.send_message(f"TS command {command} executed with result: {result}")
        else:
            PacketCommander.send_error(f"TS command {command} not found")

        # deserialized_parameters = json.loads(param) if isinstance(param, str) else param for param in parameters]
        result = function(*deserialized_parameters)
        PacketCommander.send_message(f"TS command {command} executed with result: {result}")


    @packet_handler("REQUEST_POSITION")
    def handle_request_position(packet_type: str, data: dict):
        message = {"type": "POSITION", "x":1, "y":2}
        Socket_Manager.send_all_json(message)

    @packet_handler("TRACE_OVER")
    def handle_trace_over(packet_type: str, data: dict):
        PacketCommander.send_message("Trace over request received. Creating a thread to run execution")

        thread = threading.Thread(target=TransferFunctions.run_trace_over, args=(data))
        thread .daemon = True
        thread.start()
       
    @packet_handler("SNAP_SHOT")
    def handle_snap_shot(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image_flake_hunted()
        print("Took Screenshot")

    @packet_handler("COMMAND")
    def handle_command(packet_type: str, data: dict):
        command = data.get("command")
        print(f"Received command: {command}")
        # Forward the command to all clients to ensure it appears in the command log
        Transfer_Station.send_command(command)
        #Socket_Manager.send_all_json({
        #    "type": "COMMAND",
        #    "command": command
        #})


class PacketCommander:
    """Class containing all packet commands"""
    @staticmethod
    def send_message(message: str):
        print(message)
        Socket_Manager.send_all_json({
            "type": "MESSAGE",
            "message": message
        })
    
    def send_message_no_print(message: str):
        Socket_Manager.send_all_json({
            "type": "MESSAGE",
            "message": message
        })
    
    def send_error(message: str):
        print("Error: ", message)
        Socket_Manager.send_all_json({
            "type": "ERROR",
            "message": message
        })
    
    

        