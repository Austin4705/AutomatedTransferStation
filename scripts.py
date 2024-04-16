import time
from camera import camera

def runSquareGrid(n, capture_func, inc, incXFunc, incYFunc, time_delay):
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
                incYFunc(inc)
                time.sleep(time_delay)

                capture_func(i, j, c)
                c += 1
        else:
            for a in range(n-1):
                j -= 1
                incYFunc(-inc)
                time.sleep(time_delay)

                capture_func(i, j, c)
                c += 1   
        i += 1
        incXFunc(inc)
        time.sleep(time_delay)

def capFuncTest(i, j, c):
    print(f"i{i}, j{j}, c{c}")

def init(device):
    device.set_led(10)
    device.vaccum_on()
    device.send_motor("FHMX")
    device.send_motor("FHMY")


def traceOver(device, n, increment, time_delay):
    print(camera.global_list)
    the_camera = camera.global_list[1]
    the_camera.create_image_repo()
    device.move_abs('X', 12.5)
    device.move_abs('Y', 12.5)
    runSquareGrid(n, the_camera.capture_image, increment, device.move_relX, device.move_relY, time_delay)
    # device.set_led(0)
    device.vaccum_off()