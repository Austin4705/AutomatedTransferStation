import time
from camera import Camera
import cv2
from datetime import datetime
import os 

class Image_Container:
    IMAGE_REPO_NAME = "images"
    
    def __init__(self, cameraId) -> None:
        self.name = ("camera"+str(cameraId)+"-"+str(datetime.now().strftime("%d-%m-%Y-%H-%M-%S")))
        self.camera = Camera.global_list[cameraId]    
        self.create_image_repo()

    def create_image_repo(self):
            # create the directories
            try:
                os.mkdir(Image_Container.IMAGE_REPO_NAME)
            except OSError as error:
                pass
            try:
                os.mkdir(Image_Container.IMAGE_REPO_NAME+"/"+self.name)
            except OSError as error:
                pass

    def capture_image(self, i, j, c):
        self.camera.get_frame()
        filename = f"{i}-{j}-camera"
        cv2.imwrite("../"+Image_Container.IMAGE_REPO_NAME+"/"+self.name+"/"+filename+".png", self.camera.frame)

    def get_photo(self):
        pass
        
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
    print(Camera.global_list)
    images = image_container.Image_Container(1)
    runSquareGrid(n, images.capture_image, incrementX, incrementY, device.move_relX, device.move_relY, time_delay)
    # device.set_led(0)
    device.vaccum_off()