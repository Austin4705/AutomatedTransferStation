import time

# The abstract class for a transfer station instance
class Transfer_Station():

    def __init__(self):
        self.command_queue = []

        pass

    #Functions to reimplement 
    
    
    def send_command(self, command):
        print(f"Send Command: {command}-V")

    def receive_command(self):
        print("Receive Command-V")

    def moveX(self, X):
        print("Move X-V")

    def moveY(self, Y):
        print("Move Y-V")

    def moveXY(self, x, y):
        print(f"Move XY to {x}, {y}-V")
        self.moveX(x)
        self.moveY(y)

    def autoFocus(self):
        print("Auto Focus-V")


    #Functions NOT TO REIMPLEMENT

    #Takes Seconds
    def wait(self, time):
        print(f"Wait for {time} seconds-V")
        time.sleep(time)
    
   


