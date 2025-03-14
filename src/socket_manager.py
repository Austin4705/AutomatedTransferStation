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
    CONNECTIONS = set()


    # Load packet definitions
    # with open("./../shared/packet_definitions.json", "r") as f:
    #     PACKET_DEFS = json.load(f)["packets"]

    # Dictionary to store packet handlers
    packet_handlers: Dict[str, Callable] = dict()

    def start():
        """Start the WebSocket server and related tasks"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def main():
            # Create the WebSocket server
            server = await serve(Socket_Manager.conn_handler, "localhost", 8765)
            
            # We'll store tasks here so they persist
            tasks = []
            
            # Return the server and tasks for cleanup if needed
            return server, tasks
        
        # Run the server forever
        loop.run_until_complete(main())
        loop.run_forever()

    @classmethod
    def start_with_ts(cls, transfer_station):
        """Start the WebSocket server with a transfer station for sending commands"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def main():
            # Create the WebSocket server
            server = await serve(cls.conn_handler, "localhost", 8765)
            
            # Start the sending thread as a task
            sending_task = asyncio.create_task(cls.ts_sending_thread(transfer_station))
            
            # We'll store tasks here so they persist
            tasks = [sending_task]
            
            # Return the server and tasks for cleanup if needed
            return server, tasks
        
        # Run the server forever
        loop.run_until_complete(main())
        loop.run_forever()

    async def conn_handler(websocket):
        """
        Main handler that gets called on each new websocket handshake
        """
        Socket_Manager.CONNECTIONS.add(websocket)
        print(f"New connection created {websocket}")

        try:
            async for message in websocket:
                # Handle different types of messages
                if isinstance(message, str):
                    # Text message
                    # print(f"Received message: {message}")
                    Socket_Manager.handle_packet(message)
                else:
                    print(f"Received unsupported message type: {type(message)}")
                    error_data = {
                        "type": "ERROR",
                        "data": {
                            "code": 400,
                            "message": "Unsupported message type"
                        }
                    }
                    await websocket.send(json.dumps(error_data))

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Socket error: {e}")
        finally:
            Socket_Manager.CONNECTIONS.remove(websocket)
            print(f"Connection removed {websocket}")

    @classmethod
    def handle_packet(cls, message: str):
        """Handle incoming packets"""
        try:
            # Parse the message as JSON safely
            try:
                packet = json.loads(message)
            except json.JSONDecodeError:
                raise ValueError("Message is not valid JSON")

            # Ensure packet has a type
            packet_type = packet.get("type")
            if not packet_type:
                raise ValueError("Packet missing 'type' field")

            # Call the appropriate handler
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
        except ValueError as e:
            print(f"Invalid packet format: {e}")
            error_data = {
                "type": "ERROR",
                "data": {
                    "code": 400,
                    "message": str(e)
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
            }
            cls.send_all(json.dumps(error_data))

    #Not working, I dont care to validate it
    # @classmethod
    # def validate_packet_data(cls, packet_type: str, data: dict) -> bool:
    #     """Validate packet data against definition"""
    #     if packet_type not in cls.PACKET_DEFS:
    #         return False

    #     expected_fields = cls.PACKET_DEFS[packet_type]["fields"]
        
    #     for field, expected_type in expected_fields.items():
    #         if field not in data:
    #             return False
            
    #         value = data[field]
            
    #         # Type checking
    #         if expected_type == "bool" and not isinstance(value, bool):
    #             return False
    #         elif expected_type == "int" and not isinstance(value, int):
    #             return False
    #         elif expected_type == "float" and not isinstance(value, (int, float)):
    #             return False
    #         elif expected_type == "string" and not isinstance(value, str):
    #             return False

    #     return True

    @classmethod
    def default_handler(cls, packet_type: str, data: dict):
        """Default handler for unhandled packet types"""
        # print(f"Received unhandled packet type: {packet_type}")
        print("Data:", json.dumps(data, indent=2))

    @classmethod
    def send_all(cls, msg: str):
        """Send message to all connected clients"""
        # Don't use websockets.broadcast as it can cause concurrent writes
        for websocket in cls.CONNECTIONS:
            # Create a task for each send, but don't wait for it
            # This avoids blocking but still allows the event loop to manage sends
            asyncio.create_task(cls._safe_send(websocket, msg))
    
    @classmethod
    async def _safe_send(cls, websocket, msg: str):
        """Safely send a message to a websocket with error handling"""
        try:
            await websocket.send(msg)
        except websockets.exceptions.ConnectionClosed:
            # Connection already closed, remove it from CONNECTIONS
            if websocket in cls.CONNECTIONS:
                cls.CONNECTIONS.remove(websocket)
                print(f"Removed closed connection {websocket}")
        except Exception as e:
            print(f"Error sending message to {websocket}: {e}")

    @classmethod
    def send_all_json(cls, json_data: dict):
        """Send JSON data to all connected clients"""
        try:
            msg = json.dumps(json_data)
            cls.send_all(msg)
        except Exception as e:
            print(f"Error serializing JSON: {e}")

    # Socket stuff
    # Queue of incoming messages from web browser 
    # QUEUE_BUFFER_SIZE = 1000
    # CLIENT_DATA_QUEUE = Queue(QUEUE_BUFFER_SIZE)
    # def socket_dispatch_thread(TRANSFER_STATION):
    #     while True:
    #         if Socket_Manager.CLIENT_DATA_QUEUE.not_empty:
    #             string_data = Socket_Manager.CLIENT_DATA_QUEUE.get()
    #             print(f"Received message-s: {string_data}")
    #             data = json.loads(string_data)
    #             message = data.get("command")
    #             # CALL DISPATCH HERE
    #             #Socket_Manager.socket_dispatch(data, TRANSFER_STATION)


    async def ts_sending_thread(TRANSFER_STATION):
        while True:
            try:
                if TRANSFER_STATION.exist_new_sent_commands():
                    # print("Sending commands")
                    message = TRANSFER_STATION.since_last_send()
                    for m in message:
                        await asyncio.sleep(0.01)  # Small delay to prevent flooding
                        Socket_Manager.send_all(json.dumps({
                            "type": "COMMAND",
                            "command": m["command"],
                        }))

                if TRANSFER_STATION.exist_new_received_commands():
                    # print("Sending responses")
                    message = TRANSFER_STATION.since_last_receive()
                    for m in message:
                        await asyncio.sleep(0.01)  # Small delay to prevent flooding
                        Socket_Manager.send_all(json.dumps({
                            "type": "RESPONSE",
                            "response": m["response"],
                        }))
                
                # Sleep to prevent busy waiting
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error in ts_sending_thread: {e}")
                await asyncio.sleep(1)  # Sleep longer on error
