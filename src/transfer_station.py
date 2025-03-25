import time 
from datetime import datetime
from camera import Camera
from cvFunctions import CVFunctions

# The abstract class for a transfer station instance
class Transfer_Station():
    # Static list to track subclass instances
    _subclass_instances = []

    MAGNIFICATION_TRAVEL = {
        5: {"x": 1, "y": 1, "wait_time": 1},
        10: {"x": 1, "y": 1, "wait_time": 1},
        20: {"x": 1, "y": 1, "wait_time": 1},
        40: {"x": 1, "y": 1, "wait_time": 1},
        50: {"x": 1, "y": 1, "wait_time": 1},
        100: {"x": 1, "y": 1, "wait_time": 1},
    }

    def __init__(self):
        print("Initializing Transfer Station")
        self.command_queue = []
        # Add self to the static list if this is a subclass instance
        if self.__class__ != Transfer_Station:
            Transfer_Station._subclass_instances.append(self)
        
        self.send_command_history = []
        self.receive_command_history = []
        self._last_received_index = -1  # Track the last index that was retrieved
        self._last_sent_index = -1  # Track the last sent index that was retrieved

    # Class method to get all subclass instances
    @classmethod
    def get_subclass_instances(cls):
        return cls._subclass_instances

    #Functions to reimplement 
    def _send_command(self, command):
        print(f"Send Command: {command}-V")

    def moveX(self, X):
        print("Move X-V")

    def moveY(self, Y):
        print("Move Y-V")

    def moveZ(self, Z):
        print("Move Z-V")

    def moveXY(self, x, y):
        print(f"Move XY to {x}, {y}-V")
        self.moveX(x)
        self.moveY(y)

    def posX(self):
        # print("Get X Position-V")
        return 0

    def posY(self):
        # print("Get Y Position-V")
        return 0

    def posZ(self):
        # print("Get Z Position-V")
        return 0

    #Functions NOT TO REIMPLEMENT
    def autoFocus(self, camera_index=0):
        print("Auto Focus-V")
        originalposZ = self.posZ()
        current_frame = Camera.global_list[camera_index].get_frame()

        if CVFunctions.exist_color_features(current_frame):
            print("Not enough edges to auto focus")
            return
        # Sample points on either side of current Z position
        n_samples = 10
        z_range = 0.5
        z_step = z_range / n_samples
        
        edge_counts = []
        # Sample points above current position
        def initial_scan():
            for i in range(n_samples):
                z = originalposZ + (i * z_step)
                self.moveZ(z)
                self.wait(0.05)
                frame = Camera.global_list[camera_index].get_frame()
                edge_count = CVFunctions.calculate_focus_score(frame)
                edge_counts.append((z, edge_count))
        
        #Go above and below current position
        initial_scan()
        z_step = -z_step
        initial_scan()
        initial_scan()
        z_step = -z_step
        initial_scan()
        z_step = -z_step

        # Find highest and lowest nonzero focus positions
        nonzero_scores = [(z, score) for z, score in edge_counts if score > 0]
        if not nonzero_scores:
            print("No good focus scores found")
            return
        highest_z = max(nonzero_scores, key=lambda x: x[0])[0]
        lowest_z = min(nonzero_scores, key=lambda x: x[0])[0]

        # Sweep from highest to lowest with finer resolution
        fine_z_step = 0.001  # 0.001 mm resolution
        fine_edge_counts = []
        
        current_z = highest_z
        while current_z >= lowest_z:
            self.moveZ(current_z)
            self.wait(0.01)
            frame = Camera.global_list[camera_index].get_frame()
            edge_count = CVFunctions.calculate_focus_score(frame)
            fine_edge_counts.append((current_z, edge_count))
            current_z -= fine_z_step
            
        # Find z position with highest focus score
        best_z = max(fine_edge_counts, key=lambda x: x[1])[0]
         
        # Move to position with best focus
        self.moveZ(best_z)
        self.wait(0.1)

    #Takes Seconds
    def time_stamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]     
    
    def send_command(self, command):
        response = self._send_command(command)
        if(response is not None):
            self.add_response(response) 
        self.send_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'command': command,
            'response': response
        })
        return response

    def wait(self, seconds):
        print(f"Wait for {seconds} seconds-V")
        time.sleep(seconds)
    
    def send_command_history(self, depth = -1):
        print("Send Command History-V")
        if depth == -1:
            return self.send_command_history
        else:
            return self.send_command_history[-depth:]

    def receive_command(self, depth = -1):
        print("Receive Command-V")
        self._last_received_index = len(self.receive_command_history)
        return self.receive_command_history[-1]

    def receive_commands(self, depth = -1):
        print("Receive Command-V")
        self._last_received_index = len(self.receive_command_history)
        if depth == -1:
            return self.receive_command_history
        else:
            return self.receive_command_history[-depth:]
    
    def since_last_receive(self):
        if self._last_received_index == -1:
            commands = self.receive_command_history
        else:
            commands = self.receive_command_history[self._last_received_index:]
        self._last_received_index = len(self.receive_command_history)
        return commands

    def sent_commands(self, depth = -1):
        print("Sent Commands-V")
        if depth == -1:
            return self.send_command_history
        else:
            return self.send_command_history[-depth:]

    def since_last_send(self):
        if self._last_sent_index == -1:
            commands = self.send_command_history
        else:
            commands = self.send_command_history[self._last_sent_index:]
        self._last_sent_index = len(self.send_command_history)
        return commands
    
    def exist_new_sent_commands(self):
        return len(self.send_command_history) > self._last_sent_index + 1
    
    def exist_new_received_commands(self):
        return len(self.receive_command_history) > self._last_received_index + 1
    
    def add_fake_command(self, command):
        self.send_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'command': command,
            'response': "Virtual Response"
        })

    def add_response(self, response):
        self.receive_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'response': response
        })

    def add_fake_response(self, response):
        self.receive_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'response': response
        })
