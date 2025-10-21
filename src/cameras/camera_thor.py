import cv2
from datetime import datetime
import os
import numpy as np
import threading
import time
import weakref

class Camera_Thor(Camera):

    def __init__(self, cameraId, cap):
        super().__init__(cameraId, cap)