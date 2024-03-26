import asyncio
from websockets.server import serve
import json

async def echo(websocket):
    async for message in websocket:
        data = json.loads(message)
        data["sender"] = "Server"
        data["message"] = "ACK " + data["message"]
        await websocket.send(json.dumps(data))

async def start_socket(callback):
    async with serve(callback, "localhost", 8765):
        await asyncio.Future()  # run forever

# asyncio.run(start_socket())