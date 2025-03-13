from typing import Any, Dict, Callable
import json
from socket_manager import Socket_Manager
from camera import Camera
from transfer_station import Transfer_Station 
import threading
from transfer_functions import TransferFunctions
from threading import Thread
from image_container import Image_Container
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

    def __init__(self, transfer_station):
        print(f"Initializing PacketHandlers")
        Socket_Manager.packet_handlers = _handlers
        PacketHandlers.transfer_station = transfer_station
    
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

            thread = Thread(target=execute_command)
            thread.daemon = True
            thread.start()
                
        except Exception as e:
            PacketCommander.send_error(f"Handler error: {str(e)}")
            print(f"TS_COMMAND handler error: {str(e)}")

    @packet_handler("REQUEST_POSITION")
    def handle_request_position(packet_type: str, data: dict):
        message = {"type": "POSITION", "x":PacketHandlers.transfer_station.posX(), "y":PacketHandlers.transfer_station.posY()}
        Socket_Manager.send_all_json(message)

    @packet_handler("TRACE_OVER")
    def handle_trace_over(packet_type: str, data: dict):
        PacketCommander.send_message("Trace over request received. Creating a thread to run execution")

        thread = threading.Thread(target=TransferFunctions.run_trace_over, args=(data,))
        thread.daemon = True
        TransferFunctions.executing_threads[thread] = True
        thread.start()

    @packet_handler("CANCEL_EXECUTION")
    def handle_cancel_execution(packet_type: str, data: dict):
        PacketCommander.send_message(f"Cancelling execution of running operations")
        # Set the cancellation flag to stop running threads
        for thread in TransferFunctions.executing_threads:
            TransferFunctions.executing_threads[thread] = False
            print(f"Thread {thread} signaled to stop")
        PacketCommander.send_message("All operations cancelled")

    @packet_handler("SCAN_FLAKES")
    def handle_scan_flakes(packet_type: str, data: dict):
        directory = data.get("directory")
        image_container = Image_Container(PacketHandlers.transfer_station, directory)
        PacketCommander.send_message(f"Scanning flakes in {directory}")
        image_container.search_images()
        Socket_Manager.send_all_json({
            "type": "SCAN_FLAKES_RESPONSE",
            "response": "Scan completed",
            "success": True,
            "waferCount": len(image_container.metadata.get("searched", []))
        })

    @packet_handler("DRAW_FLAKES")
    def handle_draw_flakes(packet_type: str, data: dict):
        directory = data.get("directory")
        image_container = Image_Container(PacketHandlers.transfer_station, directory)
        image_container.generate_image_output()
        Socket_Manager.send_all_json({
            "type": "DRAW_FLAKES_RESPONSE",
            "response": "Wafers drawn",
            "success": True,
            "directory": directory
        })

    @packet_handler("ACK")
    def handle_ack(packet_type: str, data: dict):
        print("ACK received")
        Socket_Manager.send_all_json({
            "type": "ACK",
        })

    @packet_handler("SNAP_SHOT")
    def handle_snap_shot(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image()
        print("Took Screenshot")
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT",
            "camera": data["camera"]
        })

    @packet_handler("SNAP_SHOT_FLAKE_HUNTED")
    def handle_snap_shot_flake_hunted(packet_type: str, data: dict):
        Camera.global_list[data["camera"]].snap_image_flake_hunted()
        print("Took Screenshot")
        Socket_Manager.send_all_json({
            "type": "REFRESH_SNAPSHOT_FLAKE_HUNTED",
            "camera": data["camera"]
        })

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
    
    

        