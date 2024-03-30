import time

def runSquareGrid(n, func, inc, incXFunc, incYFunc):
    i = 0
    j = 0
    c = 0
    for k in range(n):
        func(i, j, c)
        c += inc
        if(k % 2 == 0):
            for a in range(n-1):
                j += 1
                incYFunc()
                func(i, j, c)
                c += inc
        else:
            for a in range(n-1):
                j -= 1
                incYFunc()
                func(i, j, c)
                c += inc   
        i += 1
        incXFunc()

def traceOver(device):
    device.setLed(10)
    device.vaccumOn()
    device.sendMotor("FHMX")
    device.sendMotor("FHMY")

    runSquareGrid(5, , 10, device.)

    time.sleep(2)
    print("SLEPT")
    device.setLed(0)
    device.vaccumOff()