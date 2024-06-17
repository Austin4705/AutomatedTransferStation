import socket_manager
import json

def dispatch(self, message):
    print(message)
    if message[0:2] == "X:":
        self.x_pos = float(message[2:])
    elif message[0:2] == "Y:":
        self.y_pos = float(message[2:])
    elif message[0:5] == "TEMP:":
        self.temp = float(message[5:])
    elif message[0:9] == "DONEZOOM:":
        self.donezoom = float(message[9:])
    elif message[0:5] == "PRES:":
        self.pres = float(message[5:])
    else:
        print(message)
    Socket_Manager.send_all(json.dumps({"message": message, "sender": "transfer station"}))
        # print("Unknown Packet")
