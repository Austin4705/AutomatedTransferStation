from transfer_station import Transfer_Station
from serial import Serial
import threading
from queue import Queue
import time
import os
import re

from logger import Logger


class TransferStationPrior(Transfer_Station):
    MAGNIFICATION_TRAVEL = {
        5: {"x": 1, "y": 1, "wait_time": 1},
        10: {"x": 1, "y": 1, "wait_time": 1},
        20: {"x": 0.7, "y": 0.5, "wait_time": 1},
        40: {"x": 1, "y": 1, "wait_time": 1},
        50: {"x": 1, "y": 1, "wait_time": 1},
        100: {"x": 1, "y": 1, "wait_time": 1},
    }
    def __init__(self):
        super().__init__()
        self.type = "prior"
        self.command_server = CommandServer(port=os.getenv('PRIOR_PORT', 'COM3'), baudrate=9600, timeout=0.1)

    def _send_command(self, command):
        return self.command_server.send(command)

    def _internal_to_output(self, x):
        return int(x * 100000)

    def _output_to_internal(self, x):
        if x is None:
            raise ValueError("No response received from Prior stage")

        if isinstance(x, bytes):
            x = x.decode('ascii', errors='ignore')

        if isinstance(x, str):
            x = x.strip()
            for delimiter in ("\r", "\n"):
                if delimiter in x:
                    x = x.split(delimiter, 1)[0]
            match = re.search(r"-?\d+(?:\.\d+)?", x)
            if match:
                x = match.group(0)
            else:
                raise ValueError(f"Unable to parse numeric value from response: {x!r}")

        return float(x) / 100000

    def moveX(self, X):
        self._send_command(f"GX {self._internal_to_output(X)}")

    def moveY(self, Y):
        self._send_command(f"GY {self._internal_to_output(Y)}")

    def moveZ(self, Z):
        self._send_command(f"GZ {self._internal_to_output(Z)}")

    def moveXY(self, x, y):
        self._send_command(f"G {self._internal_to_output(x)} {self._internal_to_output(y)}")

    def moveXRel(self, X):
        self._send_command(f"GR {self._internal_to_output(X)} 0")

    def moveYRel(self, Y):
        self._send_command(f"GR 0 {self._internal_to_output(Y)}")

    def moveZRel(self, Z):
        self._send_command(f"GR 0 0 {self._internal_to_output(Z)}")

    def moveXYRel(self, X, Y):
        self._send_command(f"GR {self._internal_to_output(X)} {self._internal_to_output(Y)}")

    def posX(self):
        return self._output_to_internal(self._send_command("PX"))

    def posY(self):
       return self._output_to_internal(self._send_command("PY"))

    def posZ(self):
        return self._output_to_internal(self._send_command("PZ"))


class CommandServer:

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 0.1):
        self.message_history = []
        self.response_queue = Queue()
        self.running = True
        
        try:
            self.device = Serial(port=port, baudrate=baudrate, timeout=timeout)
            time.sleep(0.5)
            print(f'CommandServer: Connected to {port}')
        except Exception as e:
            print(f'CommandServer: Failed to connect to {port}: {e}')
        
        self.listener_thread = threading.Thread(target=self._listen_serial, daemon=True)
        self.listener_thread.start()

    def _listen_serial(self):
        while self.running:
            try:
                while not self.response_queue.empty():
                    if not self.response_queue.queue[0]["sent"]:
                        message = self.response_queue.queue[0]["message"]
                        self.response_queue.queue[0]["sent"] = True
                        self.response_queue.queue[0]["sent_time"] = time.time()
                    self.device.write(bytes(f"{message}\r\n", 'ascii'))
                    reading = self.device.readline()
                    if reading:
                        decoded = reading.decode('ascii', errors='ignore').strip()
                        if decoded:
                            self.response_queue.queue[0]["response"] = decoded
                            self.response_queue.queue[0]["processed"] = True
                            self.response_queue.get()
                time.sleep(0.05)
                        
            except Exception as e:
                if self.running:
                    print(f'CommandServer: Error reading serial: {e}')
                break

    def send(self, command, wait_response=True):
        """
        Send a command to the Prior stage
        
        Args:
            command: Command string to send
            wait_response: Whether to wait for a response
            timeout: Maximum time to wait for response (seconds)
            
        Returns:
            Response string if wait_response=True, otherwise None
        """
        try:
            data = {
                "message": command,
                "response": "",
                "sent": False,
                "processed": False
            }
            self.response_queue.put(data)
            if not wait_response:
                return None

            current_time = time.time() 
            while time.time() - current_time < 2.0:
                if data["processed"]:
                    return data["response"]
                time.sleep(0.05)
            
        except Exception as e:
            print(f'CommandServer: Error sending command "{command}": {e}')
            return None

    def close(self):
        self.running = False
        if self.device and self.device.is_open:
            self.device.close()
            print('CommandServer: Serial connection closed')

    def __del__(self):
        self.close()

