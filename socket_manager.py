import asyncio
from websockets.server import serve
import json
from queue import Queue
import websockets

'''
This class handles the websockets that are used to communicate with the UI. 
All you really have to know is that it has a queue of jsons that represent incoming messages and a function to send jsons to the clients.
'''
class Socket_Manager:
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
        asyncio.run(Socket_Manager.start_socket_server())