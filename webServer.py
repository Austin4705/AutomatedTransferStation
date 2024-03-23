from flask import Flask, render_template, Response, jsonify
import cv2
from camera import camera as Camera
from stationCommunication import transferStation
import json
from enum import Enum
import time
import os
import scripts
import threading

app = Flask(__name__)
appSetup = False

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


def startupFlaskApp():
    app.run(host='127.0.0.1', port="5000", debug=True, use_reloader=False)
    print("Server Startup Done!")
    appSetup = True

if __name__ == '__main__':
    # os.environ["PYTHONUNBUFFERED"] = "0"
    # app.run(host='127.0.0.1', port="5000", debug=True)
    threading.Thread(target=startupFlaskApp).start()
    while(not startupFlaskApp):
        pass
    x = input()
    station = transferStation('COM3', 'COM4')
    scripts.traceOver(station)
    
    # while(True):
        # station.sendCommandStation(input())
        # station.moveREL('X',10)
        # time.sleep(1)
        # station.sendCommandStation("")
    # x = input()
    print("Closing Out")
    # station.endCommunication()


    

    
    
    
