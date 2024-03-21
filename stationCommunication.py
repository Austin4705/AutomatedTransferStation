from serial import Serial
import threading

class transferStation:
    class serialObj:
        def __init__(self, port, handleData) -> None:
            self.port = port
            self.startCommunication(port)
            self.handleData = handleData

        def startCommunication(self, port):
            self.device = Serial(port=port, baudrate=9600, timeout=.1) 
            self.thread = threading.Thread(target=self.receiveCommandStation  )
                                    #   ,args=(self.device))
            self.thread.start()

        def receiveCommandStation(self, device):
            while True:
                reading = device.readline()
                readStr = str(reading)
                if readStr != "b\'\'":
                    self.handleData(readStr[2:len(readStr)-5])

        def endCommunication(self):
            self.thread.join()
            self.device.close()

    def __init__(self, portCtrl1, portCtrl2) -> None:
        self.motorDevice = transferStation.serialObj(portCtrl1, transferStation.handleData)

        # self.device1, self.thread1 = self.startCommunication(portCtrl1)
        # device2, thread2 = self.startCommunication(portCtrl2)

    # def startCommunication(self, port):
    #     device = Serial(port=port, baudrate=9600, timeout=.1) 
    #     thread = threading.Thread(target=self.receiveCommandStation  )
    #                             #   ,args=(self.device))
    #     thread.start()
    #     return [device, thread]
        

    def sendCommandStation(self, command):
        self.device1.write(bytes(f"{command}\r\n", 'ascii'))
    
    def handleData(self, data):
        print(data)
        pass

    def moveABS(self, x, y):
        self.sendCommandStation(f"ABS{x}{y}")
    
    def moveREL(self, axis, val):
        self.sendCommandStation(f"REL{axis}{val}")

   
    

    