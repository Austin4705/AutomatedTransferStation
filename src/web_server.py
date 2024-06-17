from flask import Flask, render_template, Response, jsonify
from camera import camera
import logging

app = Flask(__name__)

@app.route('/video_feed0')
def video_feed0():
    return Response(camera.generate_video(camera.global_list[0]),
    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed1')
def video_feed1():
    return Response(camera.generate_video(camera.global_list[1]),
    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(camera.generate_video(camera.global_list[2]),
    mimetype='multipart/x-mixed-replace; boundary=frame')

def startup_flask_app():
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.run(host='127.0.0.1', port="5000", debug=True, use_reloader=False)
