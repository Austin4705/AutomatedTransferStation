from typing import Any, Dict, Callable
import json
from socket_manager import Socket_Manager
from camera import Camera
from transfer_station import Transfer_Station 


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

    @packet_handler("REQUEST_POSITION")
    def handle_request_position(packet_type: str, data: dict):
        message = {"type": "POSITION", "x":1, "y":2}
        Socket_Manager.send_all_json(message)

    @packet_handler("TRACE_OVER")
    def handle_trace_over(packet_type: str, data: dict):
        print("Trace over request received")
        
        # Check if flakes data is provided
        if "flakes" in data and isinstance(data["flakes"], list):
            flakes = data["flakes"]
            print(f"Processing {len(flakes)} flakes")
            
            # Get speed parameter (default to 50% if not provided)
            speed = data.get("speed", 50)
            print(f"Trace over speed: {speed}%")
            
            try:
                for i, flake in enumerate(flakes):
                    flake_id = flake.get("id", i+1)
                    top_right = flake.get("topRight", {})
                    bottom_left = flake.get("bottomLeft", {})
                    
                    # Extract coordinates
                    tr_x = top_right.get("x")
                    tr_y = top_right.get("y")
                    bl_x = bottom_left.get("x")
                    bl_y = bottom_left.get("y")
                    
                    print(f"Flake {flake_id}:")
                    print(f"  Top Right: ({tr_x}, {tr_y})")
                    print(f"  Bottom Left: ({bl_x}, {bl_y})")
                    
                    # Here you would add the actual trace over functionality
                    # For example, moving to each coordinate and performing actions
                    # The speed parameter can be used to adjust the movement speed
                
                # Send a success response back to the client
                Socket_Manager.send_all_json({
                    "type": "TRACE_OVER_RESULT",
                    "success": True,
                    "message": f"Successfully processed {len(flakes)} flakes for trace over at {speed}% speed",
                    "flakeCount": len(flakes)
                })
                
                # Also send a command result for backward compatibility
                Socket_Manager.send_all_json({
                    "type": "COMMAND_RESULT",
                    "message": f"Successfully processed {len(flakes)} flakes for trace over at {speed}% speed"
                })
            except Exception as e:
                error_message = f"Error processing flakes: {str(e)}"
                print(error_message)
                Socket_Manager.send_all_json({
                    "type": "TRACE_OVER_RESULT",
                    "success": False,
                    "message": error_message
                })
                Socket_Manager.send_all_json({
                    "type": "ERROR",
                    "message": error_message
                })
        else:
            error_message = "No flakes data provided in TRACE_OVER packet"
            print(error_message)
            Socket_Manager.send_all_json({
                "type": "TRACE_OVER_RESULT",
                "success": False,
                "message": error_message,
                "flakeCount": 0
            })
            Socket_Manager.send_all_json({
                "type": "ERROR",
                "message": error_message
            })
        
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
