import asyncio
import json
import websockets
import inspect
from queue import Queue
from typing import Any, Dict, Callable
from websockets.asyncio.server import serve

class Socket_Manager:
    """
    This class handles the websockets that are used to communicate with the UI.
    All you really have to know is that it has a queue of jsons that represent incoming messages and a function to send jsons to the clients.
    """
    CONNECTIONS = set()
    packet_handlers: Dict[str, Callable] = dict()

    @classmethod
    def start(cls, _packet_handler):
        packet_handler = _packet_handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def main():
            server = await serve(Socket_Manager.conn_handler, "localhost", 8765)
        
        loop.run_until_complete(main())
        loop.run_forever()

    async def conn_handler(websocket):
        Socket_Manager.CONNECTIONS.add(websocket)
        print(f"New connection created {websocket}")

        try:
            async for message in websocket:
                if isinstance(message, str):
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

    def handle_packet(message: str):
        try:
            try:
                packet = json.loads(message)
            except json.JSONDecodeError:
                raise ValueError("Message is not valid JSON")
            packet_type = packet["type"]
            handler = Socket_Manager.packet_handlers.get(packet_type, Socket_Manager.default_handler)
            handler(packet_type, packet)

        except Exception as e:
            print(f"Error handling packet: {e}")
            error_data = {
                "type": "ERROR",
                "data": {
                    "code": 500,
                    "message": str(e)
                }
            }
            self.send_error(str(e))

    def default_handler(packet_type: str, data: dict):
        """Default handler for unhandled packet types"""
        print("Data:", json.dumps(data, indent=2))

    async def _safe_send(websocket, msg: str):
        try:
            await websocket.send(msg)
        except websockets.exceptions.ConnectionClosed:
            if websocket in Socket_Manager.CONNECTIONS:
                Socket_Manager.CONNECTIONS.remove(websocket)
                print(f"Removed closed connection {websocket}")
        except Exception as e:
            print(f"Error sending message to {websocket}: {e}")

    async def _send_all_async(cls, msg: str):
        for websocket in Socket_Manager.CONNECTIONS:
            try:
                await Socket_Manager._safe_send(websocket, msg)
            except Exception as e:
                print(f"Error in _send_all_async: {e}")

    def send_all_json(json_data: dict):
        try:
            msg = json.dumps(json_data)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.call_soon_threadsafe(lambda: asyncio.create_task(Socket_Manager._send_all_async(msg)))
        except Exception as e:
            print(f"Error serializing JSON: {e}")

    def send_message_no_print(message: str):
        Socket_Manager.send_all_json({
            "type": "MESSAGE",
            "message": message
        })

    def send_message(message: str):
        print(message)
        Socket_Manager.send_message_no_print(message)

    def send_error(message: str):
        print("Error: ", message)
        Socket_Manager.send_message_no_print(message)