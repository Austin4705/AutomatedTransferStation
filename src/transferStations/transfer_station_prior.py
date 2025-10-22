from transfer_station import Transfer_Station
from serial import Serial
import threading
from queue import Queue
import time
import os

class TransferStationPrior(Transfer_Station):
    def __init__(self):
        super().__init__()
        self.type = "prior"
        self.command_server = CommandServer(port=os.getenv('PRIOR_PORT', 'COM3'), baudrate=9600, timeout=0.1)

    def _send_command(self, command):
        return self.command_server.send(command)

    def _internal_to_output(self, x):
        return int(x * 100000)

    def _output_to_internal(self, x):
        return float(x) / 100000

    def moveX(self, X):
        self._send_command(f"GX {self._internal_to_output(X)}")

    def moveY(self, Y):
        self._send_command(f"GY {self._internal_to_output(Y)}")

    def moveZ(self, Z):
        self._send_command(f"GZ {self._internal_to_output(Z)}")

    def moveXY(self, x, y):
        self._send_command(f"G {self._internal_to_output(x)} {self._internal_to_output(y)}")

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
                reading = self.device.readline()
                if reading:
                    decoded = reading.decode('ascii', errors='ignore').strip()
                    if decoded:
                        self.message_history.append(decoded)
                        self.response_queue.put(decoded)
            except Exception as e:
                if self.running:
                    print(f'CommandServer: Error reading serial: {e}')
                break

    def send(self, command, wait_response=True, timeout=2.0):
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
            while not self.response_queue.empty():
                self.response_queue.get_nowait()
            self.device.write(bytes(f"{command}\r\n", 'ascii'))
            if wait_response:
                try:
                    response = self.response_queue.get(timeout=timeout)
                    return response
                except:
                    print(f'CommandServer: Timeout waiting for response to: {command}')
                    return None
            return None
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

