import asyncio
from websockets.asyncio.server import serve
import json
from queue import Queue
import websockets

class Socket_Manager:
    """
    This class handles the websockets that are used to communicate with the UI.
    All you really have to know is that it has a queue of jsons that represent incoming messages and a function to send jsons to the clients.
    """
    QUEUE_BUFFER_SIZE = 1000
    CONNECTIONS = set()

    # Queue of incoming messages from web browser 
    CLIENT_DATA_QUEUE = Queue(QUEUE_BUFFER_SIZE)

    # How to send data to ui
    def send_all(msg: str):
        print(f"Manager {Socket_Manager.CONNECTIONS}, {msg}")
        websockets.broadcast(Socket_Manager.CONNECTIONS, msg)

    async def consumer_handler(websocket):
        async for message in websocket:
            data = json.loads(message)
            Socket_Manager.CLIENT_DATA_QUEUE.put(data)

    async def conn_handler(websocket):
        """
        Main handler that gets called on each new websocket handshake
        """
        Socket_Manager.CONNECTIONS.add(websocket)
        print(f"New connection created {websocket}")

        try:
            async for message in websocket:
                data = json.loads(message)
                Socket_Manager.CLIENT_DATA_QUEUE.put(data)

        finally:
            Socket_Manager.CONNECTIONS.remove(websocket)
            print(f"Connection removed {websocket}")

    async def start_socket_server():
        async with serve(Socket_Manager.conn_handler, "localhost", 8765):
            await asyncio.Future()  # run forever

    def start():
        pass
        asyncio.run(Socket_Manager.start_socket_server())

    # Socket stuff
    def socket_dispatch_thread(TRANSFER_STATION):
        while True:
            if Socket_Manager.CLIENT_DATA_QUEUE.not_empty:
                data = Socket_Manager.CLIENT_DATA_QUEUE.get()
                message = data["message"]
                print(f"Received message: {message}")
                # CALL DISPATCH HERE
                #Socket_Manager.socket_dispatch(data, TRANSFER_STATION)

    def ts_sending_thread(TRANSFER_STATION):
        while True:
            if TRANSFER_STATION.exist_new_sent_commands():
                message = TRANSFER_STATION.since_last_send()
                for m in message:
                    Socket_Manager.send_all(json.dumps(m))