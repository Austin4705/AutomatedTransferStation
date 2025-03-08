# Dictionary containing travel distances for different magnifications (in micrometers)
MAGNIFICATION_TRAVEL = {
    5: {"x": 0.72, "y": 0.50, "w": 1},
    10: {"x": 0.45, "y": 0.33, "w": 1},
    20: {"x": 0.2, "y": 0.15, "w": 0.75}, #Only calibrated for 20x
    40: {"x": 0.2, "y": 0.15, "w": 0.75},
    50: {"x": 0.2, "y": 0.15, "w": 0.75},
    100: {"x": 0.2, "y": 0.15, "w": 0.75},
}

# Parameters dictionary
params = {
    "bottom_x": -8.5,      # Starting X coordinate (bottom)
    "bottom_y": 7.2679,      # Starting Y coordinate (bottom)
    "top_x": 6.128,     # Ending X coordinate (top)
    "top_y": -3.8808,     # Ending Y coordinate (top)
    "magnification": 5, # Magnification level (5,10,20,40,50,100)
    "pics_until_focus": 300,  # Number of pictures before autofocus
    "wait_time": -1,
    "focus_wait_time": 8,
    "initial_wait_time": 8,
    "save_func_params":""""C:/src/FlinderOutput/Wafer_00/Raw_pictures", 4, "pic", 0""" 
}

def generate_macro():
    # Validate magnification
    if params["magnification"] not in MAGNIFICATION_TRAVEL:
        raise ValueError("Invalid magnification. Must be one of: 5, 10, 20, 40, 50, 100")
    
    # Get travel distances for current magnification
    travel = MAGNIFICATION_TRAVEL[params["magnification"]]
    params["wait_time"] = MAGNIFICATION_TRAVEL[params["magnification"]]["w"]

    # Generate all points in the snake-like pattern
    points = []
    # Calculate number of steps in each direction
    x_steps = int(abs(params["top_x"] - params["bottom_x"]) / travel["x"])
    y_steps = int(abs(params["top_y"] - params["bottom_y"]) / travel["y"])
    
    # Generate snake-like pattern coordinates
    going_right = True

    current_x = params["bottom_x"]
    
    for y in range(y_steps + 1):
        row_y = params["bottom_y"] - (y * travel["y"])
        points.append((current_x, row_y))
        # Move left to right
        for x in range(x_steps + 1):
            if going_right:
                current_x += travel["x"]
            else:
                current_x -= travel["x"]
            points.append((current_x, row_y))
        
        going_right = not going_right
    
    # Generate commands from points
    commands = []
    pic_counter = 1

    commands.append(f"StgMoveX({params['bottom_x']});")
    commands.append(f"StgMoveY({params['bottom_y']});")
    commands.append(f"Wait({params["initial_wait_time"]});")
    commands.append("StgFocus();")
    commands.append(f"Wait({params['focus_wait_time']});")
    # Add setup commands

    for x, y in points:
        # Move to position
        commands.append(f"StgMoveX({x});")
        commands.append(f"StgMoveY({y});")
        commands.append(f"Wait({params['wait_time']});")  # Wait 5 seconds after movement
        
        # Perform autofocus if needed
        if pic_counter % params["pics_until_focus"] == 0:
            commands.append("StgFocus();")
            commands.append(f"Wait({params['focus_wait_time']});")  # Wait 20 seconds after autofocus
        
        # Take picture
        commands.append(f"SaveNext_Images({params['save_func_params']});")
        pic_counter += 1

    # Print total number of points and commands
    print(f"Generated {len(points)} points and {len(commands)} commands")


    # Write commands to file
    with open("microscope_macro.mac", "w") as f:
        f.write("\n".join(commands))
        
    print("\nCommands:")
    for cmd in commands:
        # print(cmd)
        pass
if __name__ == "__main__":
    generate_macro() 