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

# Driver module lookup — only the selected driver is imported after .env loads.
# "virtual" is built into the base classes and needs no extra import.
_CAMERA_DRIVER_MODULES = {
    "usb":  "cameras.camera_usb",
    "thor": "cameras.camera_thor",
}

_TRANSFER_STATION_DRIVER_MODULES = {
    "prior":      "transferStations.transfer_station_prior",
    "hqGraphene": "transferStations.transfer_station_winFile",
}

def _load_driver(driver_map: dict, type_name: str, label: str):
    """Import a driver module if the chosen type requires one."""
    if type_name in driver_map:
        import importlib
        mod = driver_map[type_name]
        Logger.log(f"Loading {label} driver: {mod}")
        importlib.import_module(mod)

if __name__ == "__main__":
    Logger.init_logger(Socket_Manager)
    load_dotenv("default.env")
    load_dotenv(".env", override=True)

    camera_type = os.getenv('CAMERA_TYPE', 'virtual')
    transfer_station_type = os.getenv('TRANSFER_STATION_TYPE', 'virtual')

    _load_driver(_CAMERA_DRIVER_MODULES, camera_type, "camera")
    _load_driver(_TRANSFER_STATION_DRIVER_MODULES, transfer_station_type, "transfer station")

    Logger.log("Initializing Image Container")
    IMAGE_CONTAINER = Image_Container()

    Logger.log("Starting Transfer Station")
    TRANSFER_STATION = Transfer_Station.create(transfer_station_type)

    Logger.log("Detecting and initializing cameras...")
    cameras = Camera.initialize_all_cameras(IMAGE_CONTAINER, camera_type)
    Logger.log(f"Initialized {len(Camera.global_list)} cameras: {list(Camera.global_list.keys())}")
    
    Logger.log("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.daemon = True
    flask_server_thread.start()

    Logger.log("Initializing Packet Handlers")
    packet_handlers = PacketHandlers(TRANSFER_STATION, IMAGE_CONTAINER)

    Logger.log("Starting socket")
    socket_manager_thread = threading.Thread(target=Socket_Manager.start, args=(packet_handlers,))
    socket_manager_thread.daemon = True
    socket_manager_thread.start()

    Logger.log("System Initialized. Press Enter to exit...")
    input()
    Logger.log("Stopping execution")
    PacketHandlers.transfer_functions.cancel_execution()
    Logger.save_logs()
    for camera in list(Camera.global_list.values()):
        camera.cleanup()
    sys.exit(0)
