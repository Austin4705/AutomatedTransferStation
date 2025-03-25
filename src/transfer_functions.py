import math
import packet_handlers
import camera
import threading
import time
from image_container import Image_Container
# Dictionary containing travel distances for different magnifications (in micrometers)

class TransferFunctions:
    """Class containing all transfer functions"""
    TRANSFER_STATION = None 
    executing_threads = dict()
    MAGNIFICATION_TRAVEL = None

    def __init__(self, transfer_station) -> None:
        TransferFunctions.TRANSFER_STATION = transfer_station
        TransferFunctions.MAGNIFICATION_TRAVEL = TransferFunctions.TRANSFER_STATION.MAGNIFICATION_TRAVEL
        TransferFunctions.EXECUTE_TRACE_OVER = True 
        pass

    def run_trace_over(data):
        packet_handlers.PacketCommander.send_message("Serializing a script to run trace over")
        image_container = Image_Container(TransferFunctions.TRANSFER_STATION)
        image_container.load_sent_data(data)

        command_list = TransferFunctions.generate_script(data, image_container)
        packet_handlers.PacketCommander.send_message("Running trace over")

        # Execute the command with the given parameters
        current_thread = threading.current_thread()
        for command in command_list:
            if TransferFunctions.executing_threads[current_thread]:
                while not TransferFunctions.EXECUTE_TRACE_OVER:
                    if not TransferFunctions.executing_threads[current_thread]:
                        break
                    time.sleep(0.1)
                command[0](*(command[1:]))
            else:
                break
        packet_handlers.PacketCommander.send_message("Trace over complete")
        del TransferFunctions.executing_threads[current_thread]

    def generate_script(data, image_container):
        command_list = []
        
        # Extract parameters from data
        try:
            # Optional parameters with defaults
            magnification = int(data.get("magnification", 20))
            pics_until_focus = int(data.get("pics_until_focus", 300))
            initial_wait_time = float(data.get("initial_wait_time", 8))
            focus_wait_time = float(data.get("focus_wait_time", 8))
            camera_index = int(data.get("camera_index", 0))
            wait_time = TransferFunctions.MAGNIFICATION_TRAVEL[magnification].get("wait_time", 1)
            save_images = data.get("save_images", True)

            # Get travel distances for current magnification
            travel = TransferFunctions.MAGNIFICATION_TRAVEL[magnification]

            # Log the parameters
            packet_handlers.PacketCommander.send_message(f"Trace over parameters:")

            packet_handlers.PacketCommander.send_message(f"Magnification: {magnification}x")
            packet_handlers.PacketCommander.send_message(f"Steps between autofocus: {pics_until_focus}")
            packet_handlers.PacketCommander.send_message(f"Camera index: {camera_index}")
            packet_handlers.PacketCommander.send_message(f"Save images: {save_images}")
            
            #Wafer generation
            for wafer in data.get("wafers", [{}]):
                print(f"Wafer: {wafer}")
                packet_handlers.PacketCommander.send_message(f"Wafer: {wafer}")
                bottom_left = wafer.get("bottomLeft", {})
                bottom_x = float(bottom_left.get("x"))
                bottom_y = float(bottom_left.get("y"))
                top_right = wafer.get("topRight", {})
                top_x = float(top_right.get("x"))
                top_y = float(top_right.get("y"))
            
                packet_handlers.PacketCommander.send_message(f"Bottom coordinates: ({bottom_x}, {bottom_y})")
                packet_handlers.PacketCommander.send_message(f"Top coordinates: ({top_x}, {top_y})")           
                # Validate magnification
                if magnification not in TransferFunctions.MAGNIFICATION_TRAVEL:
                    packet_handlers.PacketCommander.send_error(f"Invalid magnification: {magnification}. Must be one of: {', '.join(map(str, MAGNIFICATION_TRAVEL.keys()))}")
                    return command_list
            
            
                # Calculate number of steps in each direction
                x_steps = int(abs(top_x - bottom_x) / travel["x"])
                y_steps = int(abs(top_y - bottom_y) / travel["y"])

                packet_handlers.PacketCommander.send_message(f"Generating {x_steps+1}x{y_steps+1} = {(x_steps+1)*(y_steps+1)} points")
            
                # Generate snake-like pattern coordinates
                points = []
                going_right = True
                current_x = bottom_x
            
                for y in range(y_steps + 1):
                    row_y = bottom_y - (y * travel["y"])
                    points.append((current_x, row_y))
                
                    # Generate points for this row
                    for x in range(1, x_steps + 1):
                        if going_right:
                            next_x = current_x + travel["x"]
                        else:
                            next_x = current_x - travel["x"]
                        points.append((next_x, row_y))
                        current_x = next_x
                
                    # Change direction for next row
                    going_right = not going_right
            
                # Generate commands from points
                pic_counter = 1
                command_list.append([image_container.new_wafer])
                command_list.append([TransferFunctions.TRANSFER_STATION.moveXY, bottom_x, bottom_y]) # Add initial setup commands
                command_list.append([TransferFunctions.TRANSFER_STATION.wait, initial_wait_time]) # Initial wait
                # command_list.append([TransferFunctions.TRANSFER_STATION.autoFocus]) # Initial autofocus
                # command_list.append([TransferFunctions.TRANSFER_STATION.wait, focus_wait_time]) # Wait after autofocus
                # Visit each point in the pattern
                for x, y in points:
                    # Move to position
                    command_list.append([TransferFunctions.TRANSFER_STATION.moveXY, x, y])
                    # Perform autofocus if needed
                    if pic_counter % pics_until_focus == 0:
                        command_list.append([TransferFunctions.TRANSFER_STATION.autoFocus, camera_index])
                        # command_list.append([TransferFunctions.TRANSFER_STATION.wait, focus_wait_time])
                    # Take picture
                    command_list.append([TransferFunctions.TRANSFER_STATION.wait, wait_time])
                    if save_images:
                        command_list.append([image_container.add_image, camera_index])
                    else:
                        command_list.append([camera.Camera.global_list[camera_index].snap_image])
                    pic_counter += 1
            packet_handlers.PacketCommander.send_message(f"Generated {len(points)} points and {len(command_list)} commands")
        except Exception as e:
            packet_handlers.PacketCommander.send_error(f"Error generating script: {str(e)}")
        
        return command_list
            
