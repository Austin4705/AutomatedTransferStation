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

        def receiveCommandStation(self):
            while True:
                reading = self.device.readline()
                readStr = str(reading)
                if readStr != "b\'\'":
                    self.handleData(readStr[2:len(readStr)-5])
        def sendCommandStation(self, command):
            self.device.write(bytes(f"{command}\r\n", 'ascii'))

        def endCommunication(self):
            self.thread.join()
            self.device.close()

    def __init__(self, portCtrl1, portCtrl2) -> None:
        self.motorDevice = transferStation.serialObj(portCtrl1, transferStation.handleDataMotor)
        self.perfDevice = transferStation.serialObj(portCtrl2, transferStation.handleDataPerf)

    
    def handleDataMotor(data):
        print('COM3: ' + data)
        pass

    
    def handleDataPerf(data):
        print('COM4: ' + data)
        pass

    def sendMotor(self, msg):
        self.motorDevice.sendCommandStation(msg)

    def sendPerf(self, msg):
        self.perfDevice.sendCommandStation(msg)


    def moveABS(self, x, y):
        self.sendMotor(f"ABS{x}{y}")
    
    def moveREL(self, axis, val):
        self.sendMotor(f"REL{axis}{val}")

    def vaccumOn(self):
        self.sendPerf("VAC_ON")
   
    def vaccumOff(self):
        self.sendPerf("VAC_OFF")

    def setLed(self, val):
        self.sendPerf(f"LEV={val}")
    
    def __del__(self):
        self.motorDevice.endCommunication()
        self.perfDevice.endCommunication()
        print("ENDING COMMUNICATN")

    