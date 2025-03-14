from flask import Flask, render_template, Response, jsonify, request
from camera import Camera
import logging
import threading
import atexit
import gc
import time
import datetime

app = Flask(__name__)
# Track active streams to ensure proper cleanup
active_streams = {}
stream_lock = threading.Lock()

def startup_flask_app():
    # Set up routes for available cameras
    setup_routes()
    
    # Disable logging for cleaner output
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    
    # Register cleanup function to run at exit
    atexit.register(cleanup_resources)
    
    for camera in Camera.global_list.values():
        camera.snap_image()
        camera.snap_image_flake_hunted()

    # Start the Flask app - use processes=1 to avoid multiprocessing issues
    app.run(host='127.0.0.1', port="5000", debug=False, use_reloader=False, threaded=True)

def cleanup_resources():
    """Clean up any resources when the application exits"""
    print("Cleaning up resources...")
    
    # Close all active streams
    with stream_lock:
        for stream_id in list(active_streams.keys()):
            try:
                if isinstance(active_streams[stream_id], dict):
                    active_streams[stream_id]['active'] = False
                else:
                    active_streams[stream_id] = False
                del active_streams[stream_id]
            except:
                pass
    
    # Use the new Camera.cleanup_all method to clean up all camera instances
    Camera.cleanup_all()
    
    # Force garbage collection
    gc.collect()

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
        
        # Create flake hunted snapshot feed route
        snapshot_flake_hunted_endpoint = f'snapshot_flake_hunted{camera_id}'
        app.add_url_rule(
            f'/snapshot_flake_hunted{camera_id}',
            endpoint=snapshot_flake_hunted_endpoint,
            view_func=create_snapshot_flake_hunted_route(camera_id)
        )
        
    print(f"Created routes for {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    
# Dynamic route creation will happen in the setup_routes function
def create_video_feed_route(camera_id):
    """Create a video feed route for a specific camera"""
    def video_feed():
        # Create a unique ID for this stream
        stream_id = f"video_{camera_id}_{threading.get_ident()}"
        
        # Close any existing streams for this camera
        with stream_lock:
            for sid in list(active_streams.keys()):
                if sid.startswith(f"video_{camera_id}_") and sid != stream_id:
                    active_streams[sid]['active'] = False
                    print(f"Closing previous stream {sid} for camera {camera_id}")
        
        # Register this stream with additional information
        with stream_lock:
            active_streams[stream_id] = {
                'camera_id': camera_id,
                'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active': True
            }
        
        def generate():
            try:
                # Log when stream opens
                print(f"Video stream {stream_id} opened for camera {camera_id}")
                
                # Get the camera
                camera = Camera.global_list.get(camera_id)
                if not camera:
                    print(f"Camera {camera_id} not found")
                    return
                
                # Generate frames with a timeout to prevent blocking
                frame_count = 0
                start_time = time.time()
                
                while True:
                    # Check if this stream is still active
                    with stream_lock:
                        if stream_id not in active_streams or not active_streams.get(stream_id, {}).get('active', False):
                            print(f"Stream {stream_id} no longer active, stopping")
                            break
                    
                    # Get a frame from the camera
                    frame = camera.get_single_frame_as_response()
                    if not frame:
                        time.sleep(0.01)  # Short sleep to prevent CPU spinning
                        continue
                    
                    # Yield the frame
                    yield frame
                    
                    # Performance monitoring
                    # frame_count += 1
                    # if frame_count % 30 == 0:  # Log every 30 frames
                    #     elapsed = time.time() - start_time
                    #     fps = frame_count / elapsed if elapsed > 0 else 0
                    #     print(f"Stream {stream_id}: {frame_count} frames, {fps:.2f} FPS")
            except Exception as e:
                print(f"Error in video feed {camera_id}: {e}")
            finally:
                # Clean up when the generator exits
                with stream_lock:
                    if stream_id in active_streams:
                        del active_streams[stream_id]
                print(f"Video feed {stream_id} closed")
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    return video_feed

def create_snapshot_feed_route(camera_id):
    """Create a snapshot feed route for a specific camera"""
    def snapshot_feed():
        try:
            camera = Camera.global_list.get(camera_id)
            if not camera:
                return Response("Camera not found", status=404)
                
            # Get a single snapshot
            frame = camera.get_snapshot_as_response()
            if not frame:
                return Response("Could not get snapshot", status=500)
                
            return Response(frame, mimetype='multipart/x-mixed-replace; boundary=frame')
        except Exception as e:
            print(f"Error in snapshot feed {camera_id}: {e}")
            return Response(f"Snapshot error: {str(e)}", status=500)
    return snapshot_feed

def create_snapshot_flake_hunted_route(camera_id):
    """Create a flake hunted snapshot feed route for a specific camera"""
    def snapshot_flake_hunted_feed():
        try:
            camera = Camera.global_list.get(camera_id)
            if not camera:
                return Response("Camera not found", status=404)
                
            # Get a single flake hunted snapshot
            frame = camera.get_flake_hunted_snapshot_as_response()
            if not frame:
                return Response("Could not get flake hunted snapshot", status=500)
                
            return Response(frame, mimetype='multipart/x-mixed-replace; boundary=frame')
        except Exception as e:
            print(f"Error in flake hunted snapshot feed {camera_id}: {e}")
            return Response(f"Flake hunted snapshot error: {str(e)}", status=500)
    return snapshot_flake_hunted_feed

@app.route('/available_cameras')
def available_cameras():
    """Return a list of available camera IDs"""
    return jsonify(list(Camera.global_list.keys()))

@app.route('/active_streams')
def get_active_streams():
    """Return information about currently active video streams"""
    with stream_lock:
        stream_info = {}
        for stream_id in active_streams:
            if isinstance(active_streams[stream_id], bool):
                # Handle old format for backward compatibility
                stream_info[stream_id] = {
                    'active': active_streams[stream_id],
                    'camera_id': stream_id.split('_')[1] if '_' in stream_id else 'unknown'
                }
            else:
                # New format with more information
                stream_info[stream_id] = active_streams[stream_id]
    
    return jsonify({
        'active_stream_count': len(stream_info),
        'streams': stream_info
    })

