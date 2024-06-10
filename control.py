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
import os

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
        try:
            exec(data["message"][1:])
        except Exception  as error:
            print(f"User defined command wrong. Error:\n{error}")
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
        case _:
            print(split_msg)
            Socket_Manager.send_all("ack")



sim_test = True
if __name__ == '__main__':
    # Wait for camera server to initialize
    camera0 = camera(0)
    camera1 = camera0
    camera2 = camera0
    if not sim_test:
        camera1 = camera(1)
        camera2 = camera(2)

    print("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.start()
    print("Starting socket")


    socket_manager_thread = threading.Thread(target=Socket_Manager.start)
    socket_manager_thread.start()
    print("Socket initialized")


    TRANSFER_STATION = Transfer_Station("COM3", "COM4")
    ts_listening_therad = threading.Thread(target=socket_dispatch_thread, args=(TRANSFER_STATION,))
    ts_listening_therad.start()