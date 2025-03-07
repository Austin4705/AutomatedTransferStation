import time
from datetime import datetime

# The abstract class for a transfer station instance
class Transfer_Station():
    # Static list to track subclass instances
    _subclass_instances = []

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
    def send_command(self, command):
        print(f"Send Command: {command}-V")
        # Add command to history
        self.receive_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'response': "Virtual Response"
        })
        self.send_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'command': command,
            'response': "Virtual Response"
        })

    def moveX(self, X):
        print("Move X-V")

    def moveY(self, Y):
        print("Move Y-V")

    def moveXY(self, x, y):
        print(f"Move XY to {x}, {y}-V")
        self.moveX(x)
        self.moveY(y)

    def autoFocus(self):
        print("Auto Focus-V")

    #Functions NOT TO REIMPLEMENT

    #Takes Seconds
    def time_stamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]     

    def wait(self, time):
        print(f"Wait for {time} seconds-V")
        time.sleep(time)
    
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
        print("Since Last Receive-V")
        if self._last_received_index == -1:
            return self.receive_command_history
        else:
            newCommands = self.receive_command_history[self._last_received_index+1:]
            self._last_received_index = len(self.receive_command_history)
            return newCommands

    def sent_commands(self, depth = -1):
        print("Sent Commands-V")
        if depth == -1:
            return self.send_command_history
        else:
            return self.send_command_history[-depth:]

    def since_last_send(self):
        print("Since Last Send-V")
        if self._last_sent_index == -1:
            commands = self.send_command_history
        else:
            commands = self.send_command_history[self._last_sent_index+1:]
        self._last_sent_index = len(self.send_command_history)
        return commands
    
    def exist_new_sent_commands(self):
        return len(self.send_command_history) > self._last_sent_index + 1
    
    def exist_new_received_commands(self):
        return len(self.receive_command_history) > self._last_received_index + 1