from transfer_station import Transfer_Station

class TransferStationPrior(Transfer_Station):
    def __init__(self):
        super().__init__()
        self.type = "prior"
        self.command_server = CommandServer()

    def _send_command(self, command):
        return self.command_server.send(command)

    def moveX(self, X):
        pass

    def moveY(self, Y):
        pass

    def moveZ(self, Z):
        pass

    def moveXY(self, x, y):
        pass

    def posX(self):
        return 0

    def posY(self):
       return 0

    def posZ(self):
        return 0


class CommandServer:

    def _init_(self):
        self.message_history = []

        self.device = Serial(port='COM3', baudrate=9600, timeout=.1) 
        print('Connected to COM3')

        pass

    def send(self, command):
        pass

