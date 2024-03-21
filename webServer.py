from flask import Flask, render_template, Response, jsonify
import cv2
from camera import camera as Camera
from stationCommunication import transferStation
import json
from enum import Enum
import time
import os

app = Flask(__name__)

@app.route('/video_feed0')
def video_feed0():
    return Response(Camera.generate_video(Camera(0)),
    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed1')
def video_feed1():
    return Response(Camera.generate_video(Camera(1)),
    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(Camera.generate_video(Camera(2)),
    mimetype='multipart/x-mixed-replace; boundary=frame')




if __name__ == '__main__':
    # os.environ["PYTHONUNBUFFERED"] = "0"
    # app.run(host='127.0.0.1', port="5000", debug=True)
    print("test")
    station = transferStation('COM3')
    station.moveREL('X','-10')
    while(True):
        time.sleep(1)
        station.sendCommandStation()
    print("Hi")
    

    
    
    
