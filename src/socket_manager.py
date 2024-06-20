import asyncio
from websockets.server import serve
import json
from queue import Queue
import websockets
from camera import Camera

import scripts


class Socket_Manager:
    '''
    This class handles the websockets that are used to communicate with the UI. 
    All you really have to know is that it has a queue of jsons that represent incoming messages and a function to send jsons to the clients.
    '''
    QUEUE_BUFFER_SIZE = 1000
    CONNECTIONS = set()
    CLIENT_DATA_QUEUE = Queue(QUEUE_BUFFER_SIZE)

    # How to send data to ui
    def send_all(msg: str):
        websockets.broadcast(Socket_Manager.CONNECTIONS, msg)
    
    async def consumer_handler(websocket):
        async for message in websocket:
            data = json.loads(message)
            Socket_Manager.CLIENT_DATA_QUEUE.put(data)

    async def conn_handler(websocket):
        """
        Main handler that gets called on each new websocket handshake
        """
        print("New connection created")

        Socket_Manager.CONNECTIONS.add(websocket)

        try:
            async for message in websocket:
                data = json.loads(message)
                Socket_Manager.CLIENT_DATA_QUEUE.put(data)

        finally:
            Socket_Manager.CONNECTIONS.remove(websocket)

    async def start_socket_server():
        async with serve(Socket_Manager.conn_handler, "localhost", 8765):
            await asyncio.Future()  # run forever
    
    def start():
        pass
        asyncio.run(Socket_Manager.start_socket_server())


    # Socket stuff

    def socket_dispatch_thread(TRANSFER_STATION):    
        while True:
            if(Socket_Manager.CLIENT_DATA_QUEUE.not_empty):
                data = Socket_Manager.CLIENT_DATA_QUEUE.get()
                Socket_Manager.socket_dispatch(data, TRANSFER_STATION)

    def socket_dispatch(data, TRANSFER_STATION):
        message = data["message"]
        print(f"Received message: {message}")
        if data["message"][0] == "*":
            command = data["message"][1:]
            Socket_Manager.command_dispatch(command, TRANSFER_STATION)
        elif data["message"][0] == "^":
            TRANSFER_STATION.send_perf(data["message"][1:])
        elif data["message"][0] == "&":
            ts = TRANSFER_STATION
            try:
                exec(data["message"][1:])
            except Exception  as error:
                print(f"User defined command wrong. Error:\n{error}")
        elif data["message"][0] == "#":
            Socket_Manager.testFunction()
        elif data["message"] == "snap":
            Camera.global_list[0].snap_image()
            Socket_Manager.send_all(json.dumps({"message": "snapped", "sender": "transfer station"}))
        elif data["message"] == "moveUp":
            TRANSFER_STATION.send_motor("RELY1")
        elif data["message"] == "moveRight":
            TRANSFER_STATION.send_motor("RELX1")
        elif data["message"] == "moveLeft":
            TRANSFER_STATION.send_motor("RELX-1")
        elif data["message"] == "moveDown":
            TRANSFER_STATION.send_motor("RELY-1")
        elif data["message"] == "echo":
            Socket_Manager.send_all(json.dumps({"message": "echoACK", "sender": "transfer station"}))
            
            
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

    def testFunction():
        print("testFunction called")
