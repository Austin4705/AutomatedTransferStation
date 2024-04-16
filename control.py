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


def socket_dispatch_thread(TRANSFER_STATION):    
    while True:
        if(Socket_Manager.CLIENT_DATA_QUEUE.not_empty):
            data = Socket_Manager.CLIENT_DATA_QUEUE.get()
            socket_dispatch(data, TRANSFER_STATION)

def socket_dispatch(data, TRANSFER_STATION):
    print(data["message"])
    if data["message"][0] == "*":
        command = data["message"][1:]
        command_dispatch(command, TRANSFER_STATION)
    elif data["message"][0] == "^":
        TRANSFER_STATION.send_perf(data["message"][1:])
    elif data["message"][0] == "&":
        ts = TRANSFER_STATION
        exec(data["message"][1:])
    else:
        TRANSFER_STATION.send_motor(data["message"][0:])

def command_dispatch(msg, TRANSFER_STATION):
    split_msg = msg.split(" ")
    match split_msg[0]:
        case "init":
            scripts.init(TRANSFER_STATION)
        case "traceOver":
            # n, increment, time_delay
            scripts.traceOver(TRANSFER_STATION, int(split_msg[1]), float(split_msg[2]), float(split_msg[3]))

if __name__ == '__main__':
    # Wait for camera server to initialize
    camera0 = camera(0)
    camera1 = camera(1)
    camera2 = camera(2)

    print("Initializing Flask server")
    threading.Thread(target=web_server.startup_flask_app).start()
    

    print("Starting socket")
    threading.Thread(target=Socket_Manager.start).start()
    print("Socket initialized")
    TRANSFER_STATION = Transfer_Station("COM3", "COM4")

    threading.Thread(target=socket_dispatch_thread, args=(TRANSFER_STATION,)).start()
    
