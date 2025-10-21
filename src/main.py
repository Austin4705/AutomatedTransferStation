import threading
import json
import os
import time
import sys
import ctypes
from dotenv import load_dotenv

from socket_manager import Socket_Manager
from camera import Camera
from packet_handlers import PacketHandlers
from transfer_functions import Transfer_Functions
from transfer_station import Transfer_Station
import web_server

if __name__ == "__main__":
    load_dotenv("defualt.env")
    load_dotenv(".env", override=True)

    print("Starting Transfer Station")
    transfer_station_type = os.getenv('TRANSFER_STATION_TYPE', 'virtual')
    TRANSFER_STATION = Transfer_Station.create(transfer_station_type)

    PacketHandlers(TRANSFER_STATION)
    Transfer_Functions(TRANSFER_STATION)

    print("Detecting and initializing cameras...")
    camera_type = os.getenv('CAMERA_TYPE', 'usb')
    cameras = Camera.initialize_all_cameras(camera_type)
    
    print("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.daemon = True
    flask_server_thread.start()

    print("Starting socket")
    socket_manager_thread = threading.Thread(target=Socket_Manager.start_with_ts, args=(TRANSFER_STATION,))
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

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

