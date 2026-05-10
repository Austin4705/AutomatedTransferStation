import time
import sys
import re
from datetime import datetime
import platform

# Only import Windows-specific modules if on Windows
if platform.system() == 'Windows':
    import win32pipe
    import win32file
    import pywintypes
else:
    print("Warning: Windows-specific modules could not be imported. TransferStationWinFile will not be fully functional.")
    win32pipe = None
    win32file = None
    pywintypes = None

from ..transfer_station import Transfer_Station


@Transfer_Station.register("hqGraphene")
class TransferStationWinFile(Transfer_Station):

    MAGNIFICATION_TRAVEL = {
        5: {"x": 0.72, "y": 0.50, "wait_time": 1},
        10: {"x": 1.3, "y": 0.85, "wait_time": 1},
        20: {"x": 0.2, "y": 0.15, "wait_time": 0.75}, #Only calibrated for 20x
        40: {"x": 0.2, "y": 0.15, "wait_time": 0.75},
        50: {"x": 0.2, "y": 0.15, "wait_time": 0.75},
        100: {"x": 0.2, "y": 0.15, "wait_time": 0.75},
    }

    def __init__(self):
        super().__init__()
        self.type = "hqGrapheneServer"
        if platform.system() == 'Windows':
            self.command_server = CommandServer()
        else:
            self.command_server = DummyCommandServer()

    def _send_command(self, command):
        # print(f"Sending command: {command}")
        return self.command_server.send(command)

    def moveX(self, X):
        """Move to X coordinate"""
        cmd = f"SETPOSX{X}"
        print(f"Moving to X position: {X}")
        res = self.send_command(cmd)
        return res

    def moveY(self, Y):
        """Move to Y coordinate"""
        cmd = f"SETPOSY{Y}"
        print(f"Moving to Y position: {Y}")
        res = self.send_command(cmd)
        return res

    def moveZ(self, Z):
        """Move to Z coordinate"""
        cmd = f"SETPOSZ{Z}"
        print(f"Moving to Z position: {Z}")
        res = self.send_command(cmd)
        return res

    def moveXRel(self, X):
        """Move relative X"""
        cmd = f"SETPOSXREL{X}"
        print(f"Moving relative X: {X}")
        res = self.send_command(cmd)
        return res

    def moveYRel(self, Y):
        """Move relative Y"""
        cmd = f"SETPOSYREL{Y}"
        print(f"Moving relative Y: {Y}")
        res = self.send_command(cmd)
        return res

    def moveZRel(self, Z):
        """Move relative Z"""
        cmd = f"SETPOSZREL{Z}"
        print(f"Moving relative Z: {Z}")
        res = self.send_command(cmd)
        return res

    def moveXYRel(self, X, Y):
        """Move relative XY"""
        self.moveXRel(X)
        self.moveYRel(Y)

    def posX(self):
        """Get X position"""
        cmd = "GETPOSX"
        res = self.send_command(cmd)
        return CommandServer.get_first_double(res)

    def posY(self):
        """Get Y position"""
        cmd = "GETPOSY"
        res = self.send_command(cmd)
        return CommandServer.get_first_double(res)
    
    def posZ(self):
        """Get Z position"""
        cmd = "GETPOSZ"
        res = self.send_command(cmd)
        return CommandServer.get_first_double(res)
    
    def led_on(self):
        """Turn LED on"""
        cmd = "LEDON"
        print(f"Turning LED on")
        res = self.send_command(cmd)
        return res
    
    def led_off(self):
        """Turn LED off"""
        cmd = "LEDOFF"
        print(f"Turning LED off")
        res = self.send_command(cmd)
        return res

    def ts_autoFocus(self):
        """Auto Focus"""
        cmd = "AUTFOC"
        print(f"Auto Focusing")
        res = self.send_command(cmd)
        return res

#Command Server Class to Communicate with the HQ Graphene Transfer Station
class CommandServer:
    def __init__(self):
        self.pipe_name = r'\\.\pipe\HQ_server'
        self.message_history = []

    def send(self, data):
        try:
            handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)

            input_data = str.encode(data + '\n')
            # Send instruction data to c# server
            win32file.WriteFile(handle, input_data)

            # Receive data from Python client
            result, resp = win32file.ReadFile(handle, 64*1024)
            win32file.CloseHandle(handle)
            msg = resp.decode("utf-8").strip()

            return msg

        except pywintypes.error as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            error_msg = ""
            if e.args[0] == 2:
                error_msg = "no pipe, trying again in a sec"
                print(f"[{timestamp}] {error_msg}")
                time.sleep(1)
            elif e.args[0] == 109:
                error_msg = "broken pipe, bye bye"
                print(f"[{timestamp}] {error_msg}")
            
            # Store error in message history
            message_entry = {
                'timestamp': timestamp,
                'command': data,
                'response': error_msg,
                'error': str(e)
            }
            self.message_history.append(message_entry)
            return ""

    def get_first_double(my_string):
        if my_string is None or my_string.strip() == "OK":
            return 0
        numeric_const_pattern = r'[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?)(?:[Ee][+-]?\d+)?)'
        rx = re.compile(numeric_const_pattern)
        matches = rx.findall(my_string)
        if not matches:
            return 0
        return float(matches[0])

    def get_message_history(self):
        """Return the full message history"""
        return self.message_history

    def print_message_history(self):
        """Print the entire message history"""
        print("\nMessage History:")
        print("-" * 80)
        for entry in self.message_history:
            print(f"[{entry['timestamp']}] Command: {entry['command']}")
            print(f"Response: {entry['response']}")
            if 'error' in entry:
                print(f"Error: {entry['error']}")
            print("-" * 80)

class DummyCommandServer:
    def send(self, data):
        print(f"Sending command: {data}")
        return "OK"

    def receive_command(self):
        print("Receiving command")
        return "OK"
