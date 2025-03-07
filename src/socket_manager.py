import asyncio
from websockets.asyncio.server import serve
import json
from queue import Queue
import websockets
from typing import Any, Dict, Callable
import inspect
from packet_handlers import PacketHandlers

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
    packet_handlers: Dict[str, Callable] = PacketHandlers.handlers

    def start():
        pass
        asyncio.run(Socket_Manager.start_socket_server())

    async def start_socket_server():
        async with serve(Socket_Manager.conn_handler, "localhost", 8765):
            await asyncio.Future()  # run forever

    async def conn_handler(websocket):
        """
        Main handler that gets called on each new websocket handshake
        """
        Socket_Manager.CONNECTIONS.add(websocket)
        print(f"New connection created {websocket}")

        try:
            async for message in websocket:
                Socket_Manager.handle_packet(message)

        finally:
            Socket_Manager.CONNECTIONS.remove(websocket)
            print(f"Connection removed {websocket}")

    @classmethod
    def handle_packet(cls, message: str):
        """Handle incoming packets"""
        try:
            packet = json.loads(message)
            if isinstance(packet, str):
                packet = json.loads(packet)  # parse again if still a string
            # # print(f"Message: {message}")
            # print(f"Received message: {packet}")
            packet_type = packet.get("type")

            # Validate packet structure
            if not cls.validate_packet_data(packet_type, packet):
                raise ValueError(f"Invalid packet data for type {packet_type}")

            handler = cls.packet_handlers.get(packet_type, cls.default_handler)
            handler(packet_type, packet)


        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            error_data = {
                "type": "ERROR",
                "data": {
                    "code": 400,
                    "message": "Invalid JSON format"
                }
            }
            cls.send_all(json.dumps(error_data))
        except Exception as e:
            print(f"Error handling packet: {e}")
            error_data = {
                "type": "ERROR",
                "data": {
                    "code": 500,
                    "message": str(e)
                }
            }            # Call the appropriate handler or default handler
            cls.send_all(json.dumps(error_data))


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
    def default_handler(cls, packet_type: str, data: dict):
        """Default handler for unhandled packet types"""
        print(f"Received unhandled packet type: {packet_type}")
        print("Data:", json.dumps(data, indent=2))

    @classmethod
    def send_all(cls, msg: str):
        """Send message to all connected clients"""
        #print(f"Manager {cls.CONNECTIONS}, {msg}")
        websockets.broadcast(cls.CONNECTIONS, msg)


    # Socket stuff
    def socket_dispatch_thread(TRANSFER_STATION):
        while True:
            if Socket_Manager.CLIENT_DATA_QUEUE.not_empty:
                string_data = Socket_Manager.CLIENT_DATA_QUEUE.get()
                print(f"Received message-s: {string_data}")
                data = json.loads(string_data)
                message = data.get("command")
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