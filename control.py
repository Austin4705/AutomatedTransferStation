import asyncio
import threading
from station_com import Transfer_Station
from web_server import startup_flask_app
from socket_backend import start_socket
import scripts
import json

async def echo(websocket):
    async for message in websocket:
        data = json.loads(message)
        data["sender"] = "Server"
        data["message"] = "ACK " + data["message"]
        await websocket.send(json.dumps(data))

async def handle_socket_com(websocket):
    # async for message in websocket:
    #     data = json.loads(message)
    #     data["sender"] = "Server"
    #     data["message"] = "ACK " + data["message"]
    #     await websocket.send(json.dumps(data))

    async def send_message(msg):
        await websocket.send(msg)
    
    station = Transfer_Station('COM3', 'COM4', send_message)
    scripts.traceOver(station)

def main():
    # Wait for camera server to initialize
    threading.Thread(target=startup_flask_app).start()
    input()

    print("Flash server initialized")

    asyncio.run(start_socket(handle_socket_com))

    print("Closing Out")


if __name__ == '__main__':
    main()
    # os.environ["PYTHONUNBUFFERED"] = "0"
    # app.run(host='127.0.0.1', port="5000", debug=True)

    
    # while(True):
        # station.sendCommandStation(input())
        # station.moveREL('X',10)
        # time.sleep(1)
        # station.sendCommandStation("")
    # x = input()
    # station.endCommunication()


    