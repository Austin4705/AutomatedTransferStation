from typing import Any, Dict, Callable
import json
from socket_manager import Socket_Manager
from camera import Camera
from transfer_station import Transfer_Station 
import threading
from transfer_functions import TransferFunctions
from threading import Thread

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
        try:
            # Validate inputs
            if "command" not in data or not data["command"].strip():
                PacketCommander.send_error("Missing or empty command")
                return
                
            command = data["command"].strip()
            parameters_str = data.get("parameters", "[]").strip()
                
            if not hasattr(PacketHandlers.transfer_station, command):
                PacketCommander.send_error(f"Command '{command}' not found")
                return
                
            # Parse parameters
            try:
                # Convert curly braces to square brackets if needed
                if parameters_str.startswith('{') and parameters_str.endswith('}'):
                    parameters_str = '[' + parameters_str[1:-1] + ']'
                elif not (parameters_str.startswith('[') and parameters_str.endswith(']')):
                    parameters_str = '[' + parameters_str + ']'
                
                # Parse parameters using json or ast
                try:
                    params = json.loads(parameters_str)
                except json.JSONDecodeError:
                    import ast
                    params = ast.literal_eval(parameters_str)
                
                # Ensure params is a list
                if not isinstance(params, list):
                    params = [params]
                    
            except Exception as e:
                PacketCommander.send_error(f"Parameter parsing error: {str(e)}")
                return
                

            def execute_command():
                try:
                    result = getattr(PacketHandlers.transfer_station, command)(*params)
                    if(result is not None):
                        PacketCommander.send_message(f"TS Command executed: {result}")
                    else:
                        PacketCommander.send_message(f"TS Command executed")
                except Exception as e:
                    PacketCommander.send_error(f"Execution error: {str(e)}")

            Thread(target=execute_command).start()
                
        except Exception as e:
            PacketCommander.send_error(f"Handler error: {str(e)}")
            print(f"TS_COMMAND handler error: {str(e)}")

    @packet_handler("ACK")
    def handle_ack(packet_type: str, data: dict):
        print("ACK received")
        Socket_Manager.send_all_json({
            "type": "ACK",
        })

    @packet_handler("REQUEST_POSITION")
    def handle_request_position(packet_type: str, data: dict):
        message = {"type": "POSITION", "x":1, "y":2}
        Socket_Manager.send_all_json(message)

    @packet_handler("TRACE_OVER")
    def handle_trace_over(packet_type: str, data: dict):
        PacketCommander.send_message("Trace over request received. Creating a thread to run execution")

        thread = threading.Thread(target=TransferFunctions.run_trace_over, args=(data,))
        thread.daemon = True
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
    
    

        