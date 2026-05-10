from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from camera import Camera
import logging
import threading
import atexit
import gc
import time
import datetime
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
active_streams = {}
stream_lock = threading.Lock()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
DASHBOARD_LAYOUT_CONFIG_PATH = os.path.join(DATA_DIR, "dashboard_layout_config.json")
DEFAULT_DASHBOARD_LAYOUT = [
    {"id": "camera-1", "x": 0, "y": 0, "w": 6, "h": 6},
    {"id": "camera-2", "x": 6, "y": 0, "w": 6, "h": 6},
    {"id": "trace-over", "x": 0, "y": 6, "w": 6, "h": 5},
    {"id": "scan-flakes", "x": 6, "y": 6, "w": 6, "h": 5},
    {"id": "goto-flake", "x": 0, "y": 11, "w": 4, "h": 4},
    {"id": "commands", "x": 4, "y": 11, "w": 4, "h": 4},
    {"id": "control-panel", "x": 0, "y": 15, "w": 4, "h": 6},
    {"id": "trace-over-area", "x": 4, "y": 15, "w": 8, "h": 6},
    {"id": "packets", "x": 8, "y": 11, "w": 4, "h": 4},
    {"id": "logs", "x": 0, "y": 21, "w": 12, "h": 6},
]


def _normalize_dashboard_layout(raw_layout):
    if not isinstance(raw_layout, list):
        return None

    normalized = []
    for item in raw_layout:
        if not isinstance(item, dict):
            return None

        widget_id = item.get("id")
        x = item.get("x")
        y = item.get("y")
        w = item.get("w")
        h = item.get("h")

        if not isinstance(widget_id, str):
            return None

        try:
            normalized_item = {
                "id": widget_id,
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            }
        except (TypeError, ValueError):
            return None

        normalized.append(normalized_item)

    return normalized


def _load_dashboard_layout_from_disk():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DASHBOARD_LAYOUT_CONFIG_PATH):
        return list(DEFAULT_DASHBOARD_LAYOUT)

    try:
        with open(DASHBOARD_LAYOUT_CONFIG_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        layout = payload.get("layout") if isinstance(payload, dict) else payload
        normalized_layout = _normalize_dashboard_layout(layout)
        if normalized_layout is None:
            return list(DEFAULT_DASHBOARD_LAYOUT)

        return normalized_layout
    except Exception as e:
        print(f"Failed to load dashboard layout config: {e}")
        return list(DEFAULT_DASHBOARD_LAYOUT)

def startup_flask_app():
    setup_routes()
    
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    atexit.register(cleanup_resources)

    # Start the Flask app - use processes=1 to avoid multiprocessing issues
    port = int(os.environ.get('FLASK_PORT', '3000'))
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


@app.route('/dashboard_layout_config', methods=['GET'])
def get_dashboard_layout_config():
    layout = _load_dashboard_layout_from_disk()
    return jsonify({
        'layout': layout,
        'config_path': DASHBOARD_LAYOUT_CONFIG_PATH
    }), 200


@app.route('/dashboard_layout_config', methods=['POST'])
def save_dashboard_layout_config():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({'success': False, 'error': 'Expected JSON body'}), 400

    raw_layout = payload.get('layout') if isinstance(payload, dict) else payload
    normalized_layout = _normalize_dashboard_layout(raw_layout)

    if normalized_layout is None:
        return jsonify({
            'success': False,
            'error': "Invalid layout format. Expected list of items with id/x/y/w/h"
        }), 400

    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        with open(DASHBOARD_LAYOUT_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "layout": normalized_layout,
                "updated_at": datetime.datetime.now().isoformat(),
            }, f, indent=2)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({
        'success': True,
        'layout': normalized_layout,
        'config_path': DASHBOARD_LAYOUT_CONFIG_PATH
    }), 200
