import threading
from dotenv import load_dotenv
import os
import time

from transfer_station import Transfer_Station
from socket_manager import Socket_Manager
from camera import Camera
import data_parser
import web_server

if __name__ == '__main__':
    # Load enviroment variables
    load_dotenv()
    sim_test = os.getenv("sim_test")    

    # Wait for camera server to initialize
    camera0 = Camera(0)
    camera1 = camera0 if not sim_test else Camera(1)
    camera2 = camera0 if not sim_test else Camera(2)

    print("Loading Model")
    Camera.matGMM2DTransform(Camera.mockImage)
    print("Model Loaded")

    print("Initializing Flask server")
    flask_server_thread = threading.Thread(target=web_server.startup_flask_app)
    flask_server_thread.daemon = True
    flask_server_thread.start()
    
    print("Starting Transfer Station")
    TRANSFER_STATION = Transfer_Station(data_parser.dispatch, Socket_Manager)
    TRANSFER_STATION.start_serial() #Does threading creation

    print("Starting socket")
    socket_manager_thread = threading.Thread(target=Socket_Manager.start)
    socket_manager_thread.daemon = True
    socket_manager_thread.start()
    
    ts_listening_therad = threading.Thread(target=Socket_Manager.socket_dispatch_thread, args=(TRANSFER_STATION,))
    ts_listening_therad.daemon = True
    ts_listening_therad.start()

    
    # for i in range(1000):
    #     time.sleep(2)
    #     print(f"Sending {i}")
    #     Socket_Manager.send_all("TestMessage")

    input()
    print("Finsihed Exec")
    for thread in threading.enumerate(): 
        print(thread.name)
        print(thread.daemon)
    exit(0)