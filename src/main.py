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
from transfer_functions import TransferFunctions

from transfer_station import Transfer_Station
from transfer_station_winFile import TransferStationWinFile

if __name__ == "__main__":
    # Load configuration from JSON file
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
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
    transfer_station_name = config.get('transfer_station')
    match transfer_station_name:
        case "hqGrapheneServer":
            print("Initializing HQ Graphene Server Transfer Station")
            TRANSFER_STATION = TransferStationWinFile()
        case "base":
            print("Initializing Virtual Transfer Station")
            TRANSFER_STATION = Transfer_Station()
        case _:
            raise ValueError(f"Transfer station {transfer_station_name} not found")

    PacketHandlers(TRANSFER_STATION)
    TransferFunctions(TRANSFER_STATION)

    print("Starting socket")
    # Use the new integrated method to start WebSocket server with transfer station
    socket_manager_thread = threading.Thread(target=Socket_Manager.start_with_ts, args=(TRANSFER_STATION,))
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

    # The old separate threads are no longer needed
    # ts_sending_thread = threading.Thread(target=Socket_Manager.ts_sending_thread, args=(TRANSFER_STATION,))
    # ts_sending_thread.daemon = True
    # ts_sending_thread.start()

    print(f"System initialized with {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    print("Press Enter to exit...")
    input()

    #Fake response
    while True:
        input()
        for i in range(10):
            TRANSFER_STATION.add_fake_command(f"Fake Command {i}")
            TRANSFER_STATION.add_fake_response(f"Fake Response {i}")
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

