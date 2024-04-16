import time
from camera import camera
import image_container

def runSquareGrid(n, capture_func, incX, incY, incXFunc, incYFunc, time_delay):
    i=0
    j=0
    k = 0
    c=1
    for k in range(n):
        capture_func(i, j, c)
        c += 1
        if(k % 2 == 0):
            for a in range(n-1):
                j += 1
                incYFunc(incY)
                time.sleep(time_delay)

                capture_func(i, j, c)
                c += 1
        else:
            for a in range(n-1):
                j -= 1
                incYFunc(-incY)
                time.sleep(time_delay)

                capture_func(i, j, c)
                c += 1   
        i += 1
        incXFunc(incX)
        time.sleep(time_delay)

def capFuncTest(i, j, c):
    print(f"i{i}, j{j}, c{c}")

def init(device):
    device.set_led(10)
    device.vaccum_on()
    device.send_motor("FHMX")
    device.send_motor("FHMY")

def traceOver(device, n, incrementX, incrementY, time_delay):
    print(camera.global_list)
    images = image_container.Image_Container(1)
    runSquareGrid(n, images.capture_image, incrementX, incrementY, device.move_relX, device.move_relY, time_delay)
    # device.set_led(0)
    device.vaccum_off()