import os
import sys
import cv2
import time

from image_container import Image_Container
from cameras.camera_thor import Camera_Thor

camera_list = Camera.initialize_all_cameras(Image_Container())

camera = camera_list[0]
camera.initialize_camera()

time.sleep(10)
print("Getting frame")

frame = camera.get_frame()
cv2.imwrite('frame.png', frame)