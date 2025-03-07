from typing import Any, Dict, Callable

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
    handlers = _handlers
    
    @packet_handler("COMMAND")
    def handle_command(packet_type: str, data: dict):
        command = data["command"]
        value = data["value"]
        print(f"Executing command: {command} with value: {value}")

    @packet_handler("POSITION")
    def handle_position(packet_type: str, data: dict):
        x = data["x"]
        y = data["y"]
        z = data["z"]
        print(f"Position update - X: {x}, Y: {y}, Z: {z}")
        # Add position handling logic here
