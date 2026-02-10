from ast import Dict
from serial import Serial
import threading
from queue import Queue
import time
import os
import re



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
                time.sleep(0.01)
                        
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
                time.sleep(0.01)
            
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


command_server = CommandServer(port='COM3', baudrate=9600)
start_time = time.time()
counter = 0
while time.time() - start_time < 10:
    response = command_server.send("PZ")
    counter += 1
    print(f'Response: {response}, rate: {counter / (time.time() - start_time)}')

# device = Serial(port='COM3', baudrate=9600, timeout=0.1)

# def send(device, command):
#     device.write(bytes(f"{command}\r\n", 'ascii'))
#     response = device.readline()
#     return response

# time.sleep(0.5)

# start_time = time.time()
# counter = 0
# while time.time() - start_time < 10:
#     int
#     response1 = send(device, "PZ")
#     # response = send(device, "GR 0 0 10000")
#     counter += 1
#     print(f'Response: {response1}, , rate: {counter / (time.time() - start_time)}')
#     time.sleep(0.3)

# while True:
#     value = input()
#     if(input == "exit"):
#         break
#     print(send(device, value))