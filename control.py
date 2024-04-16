import asyncio
import threading
from transfer_station import Transfer_Station
import web_server
import scripts
import websockets
from websockets.server import serve
import json
from queue import Queue
from socket_manager import Socket_Manager
import time
from camera import camera

if __name__ == '__main__':
    # Wait for camera server to initialize
    camera0 = camera(0)
    # camera1 = camera(1)
    # camera2 = camera(2)

    print("Initializing Flask server")
    threading.Thread(target=web_server.startup_flask_app).start()
    

    print("Starting socket")
    threading.Thread(target=Socket_Manager.start).start()
    print("Socket initialized")
    TRANSFER_STATION = Transfer_Station("COM3", "COM4")

    input()
    scripts.traceOver(TRANSFER_STATION)

    # while True:
    #     if(Socket_Manager.CLIENT_DATA_QUEUE.not_empty):
    #         data = Socket_Manager.CLIENT_DATA_QUEUE.get()
    #         TRANSFER_STATION.send_motor(data["message"])
    #         print(data["message"])
    # Uncreachable