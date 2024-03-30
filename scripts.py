import time


def runSquareGrid(n, func, inc):
    i = 0
    j = 0
    c = 0
    for k in range(n):
        func(i, j, c)
        c += inc
        if(k % 2 == 0):
            for a in range(n-1):
                j += 1
                func(i, j, c)
                c += inc
        else:
            for a in range(n-1):
                j -= 1
                func(i, j, c)
                c += inc   
        i += 1

def traceOver(device):
    device.setLed(10)
    device.vaccumOn()
    # hOME AXIA
    device.sendMotor("FHMX")
    device.sendMotor("FHMY")

    

    print("SLEPT")
    device.setLed(0)
    device.vaccumOff()