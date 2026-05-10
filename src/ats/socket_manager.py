import asyncio
import json
import websockets
import inspect
import threading
import time
import os
from queue import Queue
from typing import Any, Dict, Callable
from websockets.asyncio.server import serve

from .logger import Logger

class Socket_Manager:
    """
    This class handles the websockets that are used to communicate with the UI.
    All you really have to know is that it has a queue of jsons that represent
    incoming messages and a function to send jsons to the clients.
    """
    CONNECTIONS = set()
    _connections_lock = threading.Lock()
    packet_handlers: Dict[str, Callable] = dict()
    transfer_station = None
    position_ping_enabled = True
    position_ping_interval = 1.0  # seconds

    # Store the event loop so we can safely schedule from any thread
    _loop: asyncio.AbstractEventLoop | None = None

    @classmethod
    def start(cls, _packet_handler):
        Socket_Manager.packet_handler = _packet_handler
        Socket_Manager.packet_handlers = _packet_handler.packet_handlers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        Socket_Manager._loop = loop  # store reference for cross-thread sends

        async def main():
            host = os.environ.get('WEBSOCKET_HOST', '0.0.0.0')
            port = int(os.environ.get('WEBSOCKET_PORT', '8765'))
            Logger.log(f"Starting WebSocket server on {host}:{port}")
            server = await serve(Socket_Manager.conn_handler, host, port)
        
        loop.run_until_complete(main())
        loop.run_forever()

    async def conn_handler(websocket):
        with Socket_Manager._connections_lock:
            Socket_Manager.CONNECTIONS.add(websocket)
        Logger.log(f"New connection created {websocket}")
        try:
            async for message in websocket:
                if isinstance(message, str):
                    Socket_Manager.handle_packet(message)
                else:
                    Logger.log_error(f"Received unsupported message type: {type(message)}")

        except websockets.exceptions.ConnectionClosedError as e:
            Logger.log(f"Connection closed with error: {e}")
        except Exception as e:
            Logger.log(f"Socket error: {e}")
        finally:
            with Socket_Manager._connections_lock:
                Socket_Manager.CONNECTIONS.discard(websocket)
            Logger.log(f"Connection removed {websocket}")

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
            Socket_Manager.send_error(f"Error handling packet: {e}")

    def default_handler(packet_type: str, data: dict):
        """Default handler for unhandled packet types"""
        Logger.log("Default handler, data:", json.dumps(data, indent=2))
        Logger.log("Packet handlers:", Socket_Manager.packet_handlers)


    async def _send_all_async(msg: str):
        with Socket_Manager._connections_lock:
            connections = list(Socket_Manager.CONNECTIONS)
        for websocket in connections:
            try:
                await websocket.send(msg)
            except websockets.exceptions.ConnectionClosed:
                with Socket_Manager._connections_lock:
                    Socket_Manager.CONNECTIONS.discard(websocket)
                Logger.log(f"Removed closed connection {websocket}")
            except Exception as e:
                Logger.log(f"Error sending message to {websocket}: {e}")

    def send_all_json(json_data: dict):
        """Thread-safe: schedule a send on the websocket event loop from any thread."""
        try:
            msg = json.dumps(json_data)
            loop = Socket_Manager._loop
            if loop is None or loop.is_closed():
                # Server not started yet or shut down — silently drop
                return
            loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(Socket_Manager._send_all_async(msg))
            )
        except Exception as e:
            Logger.log(f"Error serializing JSON: {e}")

    def send_message_no_print(message: str):
        Socket_Manager.send_all_json({
            "type": "MESSAGE",
            "message": message
        })

    def send_message(message: str):
        Socket_Manager.send_message_no_print(message)

    def send_error(message: str):
        Socket_Manager.send_all_json({
            "type": "ERROR",
            "data": {
                "code": 500,
                "message": message
            }
        })
