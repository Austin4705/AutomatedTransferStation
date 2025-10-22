import os
import sys
import cv2
import time

from dotenv import load_dotenv
from image_container import Image_Container
from cameras.camera_thor import Camera_Thor
from camera import Camera

load_dotenv("defualt.env")
load_dotenv(".env", override=True)


camera = Camera.create(camera_id=0, camera_type="thor")
# Camera.initialize_all_cameras(Image_Container(), "thor")
# camera = Camera.global_list[0]
print("Getting frame")
time.sleep(5)
frame = camera.get_frame()
cv2.imwrite(f'frame_{time.strftime("%Y%m%d_%H%M%S")}.png', frame)
camera.cleanup()