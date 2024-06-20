import json

import socket_manager


# File around waht to do with the data given by transfer station
def dispatch(ts, message):
    print(message)
    if message[0:2] == "X:":
        ts.x_pos = float(message[2:])
    elif message[0:2] == "Y:":
        ts.y_pos = float(message[2:])
    elif message[0:5] == "TEMP:":
        ts.temp = float(message[5:])
    elif message[0:9] == "DONEZOOM:":
        ts.donezoom = float(message[9:])
    elif message[0:5] == "PRES:":
        ts.pres = float(message[5:])
    else:
        print(message)
    socket_manager.send_all(json.dumps({"message": message, "sender": "transfer station"}))
        # print("Unknown Packet")