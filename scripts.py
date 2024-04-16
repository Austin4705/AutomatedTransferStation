import time
from camera import camera

def runSquareGrid(n, capture_func, inc, incXFunc, incYFunc):
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
                time.sleep(5)

                capture_func(i, j, c)
                c += 1
        else:
            for a in range(n-1):
                j -= 1
                incYFunc(-inc)
                time.sleep(5)

                capture_func(i, j, c)
                c += 1   
        i += 1
        incXFunc(inc)
        time.sleep(5)

def capFuncTest(i, j, c):
    print(f"i{i}, j{j}, c{c}")



def traceOver(device):
    # time.sleep(10)
    
    print("starting")
    print(camera.global_list)
    the_camera = camera.global_list[0]
    print(the_camera.name)
    the_camera.create_image_repo()
    device.set_led(10)
    device.vaccum_on()
    device.send_motor("FHMX")
    device.send_motor("FHMY")

    runSquareGrid(3, camera.global_list[0].capture_image, 1, device.move_relX, device.move_relY)

    time.sleep(2)
    print("SLEPT")
    device.set_led(0)
    device.vaccum_off()