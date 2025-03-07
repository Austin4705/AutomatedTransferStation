from typing import Any, Dict, Callable
import json
from socket_manager import Socket_Manager
from camera import Camera

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
        value = data["value"]
        print(f"Executing command: {command} with value: {value}")
        PacketHandlers.transfer_station.send_command(command, value)

    @packet_handler("COMMAND")
    def handle_command(packet_type: str, data: dict):
        command = data["command"]
        value = data["value"]
        print(f"Executing command: {command} with value: {value}")

    @packet_handler("REQUEST_POSITION")
    def handle_request_position(packet_type: str, data: dict):
        print("Requesting position")
        message = {"type": "POSITION", "x":1, "y":2}
        print(message)
        Socket_Manager.send_all_json(message)


    @packet_handler("TRACE_OVER")
    def handle_trace_over(packet_type: str, data: dict):
        print("Trace over")
        
    @packet_handler("SNAP_SHOT")
    def handle_snap_shot(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image_flake_hunted()
        print("Took Screenshot")
        
