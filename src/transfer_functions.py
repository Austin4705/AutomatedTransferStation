import packet_handlers


class TransferFunctions:
    """Class containing all transfer functions"""

    def __init__(self) -> None:
        pass

    def run_trace_over(data):
        packet_handlers.PacketCommander.send_message("Serializing a script to run trace over")
        command_list = TransferFunctions.generate_script(data)
        packet_handlers.PacketCommander.send_message("Running trace over")
        # Execute the command with the given parameters
        for command in command_list:
            command[0](*(command[1:]))

    def generate_script(data):
        command_list = []
        # Check if flakes data is provided
        if "flakes" in data and isinstance(data["flakes"], list):
            flakes = data["flakes"]
            print(f"Processing {len(flakes)} flakes")
            
            # Get speed parameter (default to 50% if not provided)
            speed = data.get("speed", 50)
            print(f"Trace over speed: {speed}%")
            
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
        return command_list
                
            
