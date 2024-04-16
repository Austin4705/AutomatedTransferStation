from serial import Serial
import threading
from queue import Queue
from socket_manager import Socket_Manager
import time
import importlib

class Serial_Obj:
    QUEUE_BUFFER_SIZE = 10000
    
    def __init__(self, port, callback) -> None:
        self.to_serial_queue = Queue(Serial_Obj.QUEUE_BUFFER_SIZE)
        # self.from_serial_queue = Queue(Serial_Obj.QUEUE_BUFFER_SIZE)
        self.port = port
        self.callback = callback

    # Used for simulating the app when there isnt a transfer station connected
    class fake_serial():
        def __init__(self, port, baudrate, timeout):
            self.printdata = True
            self.port = port
        def write(self, msg):
            if(self.printdata):
                print(f"Port: {self.port} msg: {msg}")
        def close(self):
            pass
        def readline(self):
            return bytes('', 'utf-8')            


    def add_command_buffer(self, command):
        self.to_serial_queue.put(command)

    def send_command_immediately(self, command):
        self.send_to_station(command)
    
    def start_communication(self):
        self.device = None
        if importlib.import_module("control").sim_test:
            self.device = Serial_Obj.fake_serial(port=self.port, baudrate=9600, timeout=.1)
        else:
            self.device = Serial(port=self.port, baudrate=9600, timeout=.1) 
        self.thread = threading.Thread(target=self.listen_serial)
        self.thread.start()

    def listen_serial(self):
        while True:
            reading = self.device.readline()
            readStr = str(reading)
            if readStr != "b\'\'":
                print("here")
                data = readStr[2:len(readStr)-5]
                self.callback(data)
                # self.squeue.put(f"{self.port}: {data}")

    def send_to_station(self, command):
        self.device.write(bytes(f"{command}\r\n", 'ascii'))

    def end_communication(self):
        self.thread.join()
        self.device.close()

class Transfer_Station:
    def __init__(self, portCtrl1: str, portCtrl2: str) -> None:
        print("Initializing Transfer Station...")
        self.motor_device = Serial_Obj(portCtrl1, self.message_received)
        self.perf_device = Serial_Obj(portCtrl2, self.message_received)
        self.start_serial()

        self.x_pos = 0
        self.y_pos = 0
        self.temp = 0
        self.donezoom = 0
        self.pres = 0

    def start_serial(self):
        print("Starting serial communication...")
        self.motor_device.start_communication()
        self.perf_device.start_communication()

    def message_received(self, message):
        self.dispatch(message)

    # TODO: Change structure
    def send_motor(self, msg):
        self.motor_device.send_command_immediately(msg)

    def send_perf(self, msg):
        self.perf_device.send_command_immediately(msg)

    def move_abs(self, axis, val):
        self.send_motor(f"ABS{axis}{val}")
    
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
    
    def dispatch(self, message):
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
            Socket_Manager.send_all(message)

    def __del__(self):
        self.motor_device.end_communication()
        self.perf_device.end_communication()
        print("ENDING COMMUNICATION")

    