from flask import Flask, render_template, Response, jsonify, request
from camera import Camera
import logging
import threading
import atexit
import gc
import time
import datetime
import os

app = Flask(__name__)
active_streams = {}
stream_lock = threading.Lock()

def startup_flask_app():
    setup_routes()
    
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    atexit.register(cleanup_resources)

    # Start the Flask app - use processes=1 to avoid multiprocessing issues
    port = int(os.environ.get('FLASK_PORT', '5000'))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    print(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

def cleanup_resources():
    print("Cleaning up resources...")
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
    Camera.cleanup_all()
    gc.collect()

def setup_routes():
    """Dynamically set up routes for all available cameras"""
    for camera_id in Camera.global_list.keys():

        video_endpoint = f'video_feed{camera_id}'
        app.add_url_rule(
            f'/video_feed{camera_id}',
            endpoint=video_endpoint,
            view_func=create_video_feed_route(camera_id)
        )
        
        snapshot_endpoint = f'snapshot_feed{camera_id}'
        app.add_url_rule(
            f'/snapshot_feed{camera_id}',
            endpoint=snapshot_endpoint,
            view_func=create_snapshot_feed_route(camera_id)
        )
        
        snapshot_flake_hunted_endpoint = f'snapshot_flake_hunted{camera_id}'
        app.add_url_rule(
            f'/snapshot_flake_hunted{camera_id}',
            endpoint=snapshot_flake_hunted_endpoint,
            view_func=create_snapshot_flake_hunted_route(camera_id)
        )
        
    print(f"Created routes for {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    
def create_video_feed_route(camera_id):
    def video_feed():
        stream_id = f"video_{camera_id}_{threading.get_ident()}"
        
        # Kill all old streams for this camera first
        with stream_lock:
            old_streams_to_remove = []
            for sid in list(active_streams.keys()):
                if sid.startswith(f"video_{camera_id}_") and sid != stream_id:
                    active_streams[sid]['active'] = False
                    old_streams_to_remove.append(sid)
            
            # Remove old streams immediately
            for sid in old_streams_to_remove:
                if sid in active_streams:
                    del active_streams[sid]
                    print(f"Killed old stream {sid}")
        
        # Short wait for old stream threads to notice they're dead
        if old_streams_to_remove:
            time.sleep(0.1)
        
        with stream_lock:
            active_streams[stream_id] = {
                'camera_id': camera_id,
                'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active': True
            }
        
        def generate():
            try:
                camera = Camera.global_list.get(camera_id)
                if not camera:
                    print(f"Camera {camera_id} not found")
                    return
                
                frame_count = 0
                start_time = time.time()
                
                while True:
                    with stream_lock:
                        if stream_id not in active_streams or not active_streams.get(stream_id, {}).get('active', False):
                            print(f"Stream {stream_id} no longer active, stopping")
                            break
                    
                    frame = camera.get_single_frame_as_response()
                    if not frame:
                        time.sleep(0.01)
                        continue
                    
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
                with stream_lock:
                    if stream_id in active_streams:
                        del active_streams[stream_id]
                # print(f"Video feed {stream_id} closed")
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    return video_feed

def create_snapshot_feed_route(camera_id):
    def snapshot_feed():
        try:
            camera = Camera.global_list.get(camera_id)
            if not camera:
                return Response("Camera not found", status=404)
            frame = camera.get_snapshot_as_response()
            if not frame:
                return Response("Could not get snapshot", status=500)
            return Response(frame, mimetype='multipart/x-mixed-replace; boundary=frame')
        except Exception as e:
            print(f"Error in snapshot feed {camera_id}: {e}")
            return Response(f"Snapshot error: {str(e)}", status=500)
    return snapshot_feed

def create_snapshot_flake_hunted_route(camera_id):
    def snapshot_flake_hunted_feed():
        try:
            camera = Camera.global_list.get(camera_id)
            if not camera:
                return Response("Camera not found", status=404)
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
    return jsonify(list(Camera.global_list.keys()))

@app.route('/active_streams')
def get_active_streams():
    with stream_lock:
        stream_info = {}
        for stream_id in active_streams:
            if isinstance(active_streams[stream_id], bool):
                stream_info[stream_id] = {
                    'active': active_streams[stream_id],
                    'camera_id': stream_id.split('_')[1] if '_' in stream_id else 'unknown'
                }
            else:
                stream_info[stream_id] = active_streams[stream_id]
    
    return jsonify({
        'active_stream_count': len(stream_info),
        'streams': stream_info
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'cameras': len(Camera.global_list),
        'active_streams': len(active_streams),
        'timestamp': datetime.datetime.now().isoformat()
    }), 200