import asyncio
from websockets.asyncio.server import serve
import json
from queue import Queue
import websockets
from typing import Any, Dict, Callable
import inspect

class Socket_Manager:
    """
    This class handles the websockets that are used to communicate with the UI.
    All you really have to know is that it has a queue of jsons that represent incoming messages and a function to send jsons to the clients.
    """
    QUEUE_BUFFER_SIZE = 1000
    CONNECTIONS = set()

    # Queue of incoming messages from web browser 
    CLIENT_DATA_QUEUE = Queue(QUEUE_BUFFER_SIZE)

    # Load packet definitions
    with open("./../shared/packet_definitions.json", "r") as f:
        PACKET_DEFS = json.load(f)["packets"]

    # Dictionary to store packet handlers
    packet_handlers: Dict[str, Callable] = {}

    @classmethod
    def validate_packet_data(cls, packet_type: str, data: dict) -> bool:
        """Validate packet data against definition"""
        if packet_type not in cls.PACKET_DEFS:
            return False

        expected_fields = cls.PACKET_DEFS[packet_type]["fields"]
        
        for field, expected_type in expected_fields.items():
            if field not in data:
                return False
            
            value = data[field]
            
            # Type checking
            if expected_type == "bool" and not isinstance(value, bool):
                return False
            elif expected_type == "int" and not isinstance(value, int):
                return False
            elif expected_type == "float" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "string" and not isinstance(value, str):
                return False

        return True

    @classmethod
    def packet_handler(cls, packet_type: str):
        """Decorator to register packet handlers"""
        def decorator(func):
            cls.packet_handlers[packet_type] = func
            return func
        return decorator

    @classmethod
    def default_handler(cls, packet_type: str, data: dict):
        """Default handler for unhandled packet types"""
        print(f"Received unhandled packet type: {packet_type}")
        print("Data:", json.dumps(data, indent=2))

    @classmethod
    def handle_packet(cls, packet: dict):
        """Handle incoming packets"""
        try:
            packet_type = packet.get("type")
            data = packet.get("data", {})

            # Validate packet structure
            if not cls.validate_packet_data(packet_type, data):
                raise ValueError(f"Invalid packet data for type {packet_type}")

            # Call the appropriate handler or default handler
            handler = cls.packet_handlers.get(packet_type, cls.default_handler)
            handler(packet_type, data)

        except Exception as e:
            error_data = {
                "type": "ERROR",
                "data": {
                    "code": 500,
                    "message": str(e)
                }
            }
            cls.send_all(json.dumps(error_data))

    @classmethod
    def send_all(cls, msg: str):
        """Send message to all connected clients"""
        print(f"Manager {cls.CONNECTIONS}, {msg}")
        websockets.broadcast(cls.CONNECTIONS, msg)

    async def conn_handler(websocket):
        """
        Main handler that gets called on each new websocket handshake
        """
        Socket_Manager.CONNECTIONS.add(websocket)
        print(f"New connection created {websocket}")

        try:
            async for message in websocket:
                data = json.loads(message)
                Socket_Manager.handle_packet(data)
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
                    Socket_Manager.send_all(json.dumps({
                        "type": "COMMAND",
                        "command": m["command"],
                        "value": 0
                    }))