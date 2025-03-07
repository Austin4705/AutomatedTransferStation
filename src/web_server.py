from flask import Flask, render_template, Response, jsonify 
from camera import Camera
import logging

app = Flask(__name__)

def startup_flask_app():
    # Set up routes for available cameras
    setup_routes()
    
    # Disable logging for cleaner output
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    
    # Start the Flask app
    app.run(host='127.0.0.1', port="5000", debug=True, use_reloader=False)

def setup_routes():
    """Dynamically set up routes for all available cameras"""
    # Clear any existing routes (not strictly necessary for first run)
    for camera_id in Camera.global_list.keys():
        # Create video feed route
        video_endpoint = f'video_feed{camera_id}'
        app.add_url_rule(
            f'/video_feed{camera_id}',
            endpoint=video_endpoint,
            view_func=create_video_feed_route(camera_id)
        )
        
        # Create snapshot feed route
        snapshot_endpoint = f'snapshot_feed{camera_id}'
        app.add_url_rule(
            f'/snapshot_feed{camera_id}',
            endpoint=snapshot_endpoint,
            view_func=create_snapshot_feed_route(camera_id)
        )
        
    print(f"Created routes for {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    
# Dynamic route creation will happen in the setup_routes function
def create_video_feed_route(camera_id):
    """Create a video feed route for a specific camera"""
    def video_feed():
        
        return Response(Camera.generate_video(Camera.global_list[camera_id]),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return video_feed

def create_snapshot_feed_route(camera_id):
    """Create a snapshot feed route for a specific camera"""
    def snapshot_feed():
        print(Camera.global_list[camera_id])
        return Response(Camera.get_snapped_image(Camera.global_list[camera_id]),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return snapshot_feed

@app.route('/available_cameras')
def available_cameras():
    """Return a list of available camera IDs"""
    return jsonify(list(Camera.global_list.keys()))

