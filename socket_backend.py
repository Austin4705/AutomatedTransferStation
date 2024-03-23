import asyncio
from websockets.server import serve
import json

async def echo(websocket):
    async for message in websocket:
        data = json.loads(message)
        data["sender"] = "Server"
        data["message"] = "ACK " + data["message"]
        await websocket.send(json.dumps(data))

async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())