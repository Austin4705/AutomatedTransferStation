import threading
import json
import os
import time
import sys
import ctypes
from dotenv import load_dotenv

from logger import Logger
from image_container import Image_Container
from transfer_station import Transfer_Station
from camera import Camera
import web_server
from socket_manager import Socket_Manager
from packet_handlers import PacketHandlers

if __name__ == "__main__":
    logger = Logger()
    load_dotenv("defualt.env")
    load_dotenv(".env", override=True)

    logger.log("Initializing Image Container")
    IMAGE_CONTAINER = Image_Container()

    logger.log("Starting Transfer Station")
    transfer_station_type = os.getenv('TRANSFER_STATION_TYPE', 'virtual')
    TRANSFER_STATION = Transfer_Station.create(transfer_station_type)

    logger.log("Detecting and initializing cameras...")
    camera_type = os.getenv('CAMERA_TYPE', os.getenv('CAMERA_TYPE', 'usb'))
    cameras = Camera.initialize_all_cameras(IMAGE_CONTAINER, camera_type)
    
    logger.log("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.daemon = True
    flask_server_thread.start()

    logger.log("Initializing Packet Handlers")
    packet_handlers = PacketHandlers(TRANSFER_STATION, logger)

    logger.log("Starting socket")
    socket_manager_thread = threading.Thread(target=Socket_Manager.start, args=(packet_handlers,))
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

    logger.log(f"System initialized with {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    logger.log("Press Enter to exit...")
    input()
    for thread in threading.enumerate():
        if thread.daemon:
            thread.join()
    for thread in threading.enumerate():
        print(thread.name)
        print(thread.daemon)
    logger.save_logs()
    print("Done")
    quit()
    # exit(0)

