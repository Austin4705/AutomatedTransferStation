from serial import Serial
import threading

class transferStation:
    def __init__(self, port) -> None:
        self.device = Serial(port=port, baudrate=9600, timeout=.1) 
        thread = threading.Thread(target=self.receiveCommandStation, args=(self.device))
        thread.start()

    def sendCommandStation(self, command):
        self.device.write(bytes(f"{command}\n", 'ascii'))
    
    def receiveCommandStation(self):
        while True:
            reading = self.device.readline()
            	#if reading != "b\'\'":
            if reading != "b\'\'":

                self.handleData(reading)

    def handleData(self, data):
        print(data)
        pass

    def moveABS(self, x, y):
        self.sendCommandStation(f"ABS{x}{y}")
    
    def moveREL(self, axis, val):
        self.sendCommandStation(f"REL{axis}{val}")
    

    