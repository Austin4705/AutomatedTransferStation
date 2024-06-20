from serial import Serial
import threading
from queue import Queue
import json
import os         
import time 

from socket_manager import Socket_Manager

class Transfer_Station:
    """
    This class is specifically designed for the HQ Graphene Transfer Station. 
    It is responsible for handling the serial communication between the station and the motor controller and the performance controller. 
    It also has functions to send commands to the motor controller and the performance controller.
    """
    QUEUE_BUFFER_SIZE = 1000

    def __init__(self, message_callback, socket_manager) -> None:
        print("Initializing Transfer Station...")
        self.portCtrl1 = "COM3"
        self.portCtrl2 = "COM4"

        self.motor_device = Serial_Obj(self.portCtrl1, self.dispatch)
        self.perf_device = Serial_Obj(self.portCtrl2, self.dispatch)

        self.message_callback = message_callback
        self.mainMessageQueue = Queue(Transfer_Station.QUEUE_BUFFER_SIZE)

        self.x_pos = 0
        self.y_pos = 0
        self.temp = 0
        self.donezoom = 0
        self.pres = 0
        self.vaccum_state = False
        self.led_stat = 0

    def ts_thread_loop(self, prevCmd):
        # if(self.mainMessageQueue.not_empty):
        #     command = self.mainMessageQueue.get()
        #     if command == prevCmd:

        return prevCmd
        
    
    def run_ts_sender(self):
        prevCmd = ""
        while True:
            prevCmd = self.ts_thread_loop(prevCmd)
            time.sleep(0.01)

    def start_serial(self):
        print("Starting serial communication...")
        self.motor_device.start_communication()
        self.perf_device.start_communication()
        self.thread = threading.Thread(target=self.run_ts_sender)
        self.thread.daemon = True
        self.thread.start()

    def dispatch(self, message):
        Socket_Manager.send_all(json.dumps({"message": message, "sender": "transfer station"}))
        if message[0:2] == "X:":
            self.x_pos = float(message[2:])
        elif message[0:2] == "Y:":
            self.y_pos = float(message[2:])
        elif message[0:5] == "TEMP:":
            self.temp = float(message[5:])
        elif message[0:9] == "DONEZOOM:":
            self.donezoom = float(message[9:])
        elif message[0:5] == "PRES:":
            self.pres = float(message[5:])
        else:
            print(message)

    # TODO: Change structure
    def send_motor(self, msg):
        self.motor_device.send_to_station(msg)

    def send_perf(self, msg):
        self.perf_device.send_to_station(msg)

    def move_abs(self, x, y):
        self.send_motor(f"ABS{x}{y}")
    
    def move_rel(self, axis, val):
        self.send_motor(f"REL{axis}{val}")

    def move_relX(self, val):
        self.send_motor(f"RELX{val}")

    def move_relY(self, val):
        self.send_motor(f"RELY{val}")

    def vaccum_on(self):
        self.send_perf("VAC_ON")
   
    def vaccum_off(self):
        self.send_perf("VAC_OFF")

    def set_led(self, val):
        self.send_perf(f"LEV={val}")

    def __del__(self):
        print("ENDING COMMUNICATION TO TRANSFER STATION...")
        self.motor_device.end_communication()
        self.perf_device.end_communication()
        print("COMMUNICATION ENDED")


class Serial_Obj:
    
    def __init__(self, port, callback) -> None:
        self.port = port
        self.callback = callback
        self.sim_test = os.getenv("sim_test")
        self.sim_test = bool(self.sim_test)
        
    def start_communication(self):
        if self.sim_test:
            print("Starting Mock Serial")
            self.device = Serial_Obj.MockSerial()
        else:
            print("Starting serial")
            self.device = Serial(port=self.port, baudrate=9600, timeout=.1) 
        self.thread = threading.Thread(target=self.listen_serial)
        self.thread.daemon = True
        self.thread.start()

    def listen_serial(self):
        while True:
            reading = self.device.readline()
            readStr = str(reading)
            if readStr != "b\'\'":
                data = readStr[2:len(readStr)-5]
                self.callback(data)
                # self.squeue.put(f"{self.port}: {data}")

    def send_to_station(self, command):
        self.device.write(bytes(f"{command}\r\n", 'ascii'))

    def end_communication(self):
        self.thread.join()
        self.device.close()

    class MockSerial():
        def init(self, port, baudrate, timeout):
            pass
        def start_communication(self):
            pass
        def write(self, b, /):
            print(f"Mock Serial Write: {str(b)[2:len(str(b))-5]}")
        def readline(self):
            return "b\'\'"
        def close(self):
            pass

