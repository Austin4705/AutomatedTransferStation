import asyncio
import threading
from transfer_station import Transfer_Station
from web_server import startup_flask_app
import scripts
import websockets
from websockets.server import serve
import json
from queue import Queue
from socket_manager import Socket_Manager


if __name__ == '__main__':
    # Wait for camera server to initialize
    print("Initializing Flask server")
    threading.Thread(target=startup_flask_app).start()

    print("Starting socket")
    threading.Thread(target=Socket_Manager.start).start()
    print("Socket initialized")
    TRANSFER_STATION = Transfer_Station("COM3", "COM4")

    while True:
        if(Socket_Manager.CLIENT_DATA_QUEUE.not_empty):
            data = Socket_Manager.CLIENT_DATA_QUEUE.get()
            TRANSFER_STATION.send_motor(data["message"])
            print(data["message"])
    # Uncreachable