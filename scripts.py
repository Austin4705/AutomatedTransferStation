import time

def traceOver(device):
    device.setLed(10)
    device.vaccumOn()
    device.sendMotor("FHMX")
    device.sendMotor("FHMY")

    for i in range(3):
        if(i % 2 == 0):
            for j in range(3):
        else:
            for j in range(3, -1):
                print("{}")

    time.sleep(2)
    print("SLEPT")
    device.setLed(0)
    device.vaccumOff()