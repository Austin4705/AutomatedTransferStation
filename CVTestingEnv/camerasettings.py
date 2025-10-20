import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def _():
    import asyncio
    import threading

    # import scripts
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

    # import tisgrabber
    print("Cell ran")
    return (cv2,)


@app.cell
def _(cv2):
    # Initialize video capture from default camera (usually 0)
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera")
        exit
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
    # ret, frame = cap.read()
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
    # counter = 0
    # pic_counter = 1000
    # while True:
    #     # Capture frame-by-frame
    #     ret, frame = cap.read()
    #     # if counter % pic_counter == 0:
    #     # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
    #     # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)
    #     counter += 1
    #
    #     # If frame is read correctly ret is True
    #     if not ret:
    #         print("Error: Can't receive frame")
    #         break
    #
    #     cv2.imshow("Video Stream", frame)
    #
    #     # Press 'q' to exit
    #     if cv2.waitKey(1) & 0xFF == ord("q"):
    #         break
    #
    # # When everything is done, release the capture and destroy windows
    # cap.release()
    # cv2.destroyAllWindows()
    return


if __name__ == "__main__":
    app.run()
