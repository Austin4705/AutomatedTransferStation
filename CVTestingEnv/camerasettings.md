---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.17.1
  kernelspec:
    display_name: automatedTransfer
    language: python
    name: python3
---

```python
import asyncio
import threading
import scripts
import json
import time
import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sklearn.cluster
import skimage
from skimage import morphology
import argparse
import matplotlib.cm as cm

from GMMDetector import MaterialDetector

import tisgrabber
```

```python
# Initialize video capture from default camera (usually 0)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
ret, frame = cap.read()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
counter = 0
pic_counter = 1000
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if counter % pic_counter == 0:
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
    counter += 1

    
    # If frame is read correctly ret is True
    if not ret:
        print("Error: Can't receive frame")
        break
    
    cv2.imshow('Video Stream', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()

```
