from flask import Flask, render_template, Response, jsonify
import cv2
from camera import camera as Camera

app = Flask(__name__)



video_stream = Camera(0)

@app.route('/')
def index():
    return render_template('index.html')

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
    app.run(host='127.0.0.1', port="5000", debug=True)