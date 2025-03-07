from socket_manager import Socket_Manager

@Socket_Manager.packet_handler("COMMAND")
def handle_command(packet_type: str, data: dict):
    command = data["command"]
    value = data["value"]
    print(f"Executing command: {command} with value: {value}")
    # Add command handling logic here

@Socket_Manager.packet_handler("POSITION")
def handle_position(packet_type: str, data: dict):
    x = data["x"]
    y = data["y"]
    z = data["z"]
    print(f"Position update - X: {x}, Y: {y}, Z: {z}")
    # Add position handling logic here 