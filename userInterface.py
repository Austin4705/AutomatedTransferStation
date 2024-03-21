from enum import Enum
import json

class userInt:
    packetTypes = Enum('packetTypes', ['moveABS', 'moveREL', 'transferFILE'])

    def getMessageApp(jsonStr):
        jsonObj = json.loads(jsonStr)
        packetID = jsonObj["packetID"]
        match packetID:
            case 0:
                pass
            case 1:
                pass
            case 2: 
                pass 
            case _:
                print("PACKETIDNOTFOUND\n"+jsonStr)

    def sendMessageApp(json):
        pass
