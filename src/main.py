import threading
import json
import os
import time
import sys
import ctypes
from transferStations.transfer_station_HQ_Old import Transfer_Station, data_parser
from socket_manager import Socket_Manager
from camera import Camera
import web_server
from cvFunctions import CVFunctions


def raise_exception(thread):
    thread_id = thread.native_id
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        thread_id, ctypes.py_object(SystemExit)
    )
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print("Exception raise failure")


if __name__ == "__main__":
    # Load configuration from JSON file
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
    sim_test = config.get('sim_test', False)
    print(f"Simulation test mode: {sim_test}")
    
    # Initialize cameras using the new intelligent detection system
    print("Detecting and initializing cameras...")
    cameras = Camera.initialize_all_cameras()
    
    print("Loading Model")
    CVFunctions()
    print("Model Loaded")
    
    print("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.daemon = True
    flask_server_thread.start()

    # Everything up until here is fully working

    print("Starting Transfer Station")
    TRANSFER_STATION = Transfer_Station(data_parser.dispatch, Socket_Manager)
    TRANSFER_STATION.start_serial()  # Does threading creation

    print("Starting socket")
    socket_manager_thread = threading.Thread(target=Socket_Manager.start)
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

    ts_listening_thread = threading.Thread(
        target=Socket_Manager.socket_dispatch_thread, args=(TRANSFER_STATION,)
    )
    ts_listening_thread.daemon = True
    ts_listening_thread.start()

    print(f"System initialized with {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    print("Press Enter to exit...")
    input()

    for thread in threading.enumerate():
        if thread.daemon:
            thread.join()
    for thread in threading.enumerate():
        print(thread.name)
        print(thread.daemon)
    print("Done")
    quit()
    # exit(0)

