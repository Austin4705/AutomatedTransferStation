import threading
import json
import os
import time
import sys
import ctypes
from socket_manager import Socket_Manager
from camera import Camera
import web_server
from cvFunctions import CVFunctions
from packet_handlers import PacketHandlers
from transfer_station import Transfer_Station

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
    TRANSFER_STATION = Transfer_Station()
    PacketHandlers.transfer_station = TRANSFER_STATION
    PacketHandlers()

    print("Starting socket")
    # Starting the tread  that generally runs the socket server
    socket_manager_thread = threading.Thread(target=Socket_Manager.start)
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

    # Starting the thread that listens from the sockets and sends them to the right place 
    # (handles incoming communication from the UI)
    ts_listening_thread = threading.Thread(target=Socket_Manager.socket_dispatch_thread, args=(TRANSFER_STATION,))
    ts_listening_thread.daemon = True
    ts_listening_thread.start()

    # Starting the thread that sends the commands to the transfer station
    ts_sending_thread = threading.Thread(target=Socket_Manager.ts_sending_thread, args=(TRANSFER_STATION,))
    ts_sending_thread.daemon = True
    ts_sending_thread.start()

    print(f"System initialized with {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    print("Press Enter to exit...")
    input()

    #Fake response
    while True:
        input()
        for i in range(10):
            TRANSFER_STATION.send_command(f"Fake Response {i}")
        print("Done")

    for thread in threading.enumerate():
        if thread.daemon:
            thread.join()
    for thread in threading.enumerate():
        print(thread.name)
        print(thread.daemon)
    print("Done")
    quit()
    # exit(0)

