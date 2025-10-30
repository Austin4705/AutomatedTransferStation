import { useCallback } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import useAppendConsole from "./useAppendConsole";
import { PacketManager } from "../packets/PacketHandler";

export const useSendJSON = () => {
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();

  const sendJson = useCallback(
    (data: any) => {
      if (jsonState.sendJsonMessage) {
        if (PacketManager.isInitialized && !PacketManager.isInitialized()) {
          console.warn("Packet manager not initialized yet. Initializing now...");
          PacketManager.initialize().then(() => {
            console.log("Packet manager initialized from useSendJSON");
          });
        }

        appendConsole({
          sender: "Client",
          message: JSON.stringify(data),
        });
        
        const outgoingEvent = new CustomEvent('outgoingMessage', { 
          detail: data 
        });
        window.dispatchEvent(outgoingEvent);
        
        jsonState.sendJsonMessage(data);
      } else {
        console.error("WebSocket connection not established", { 
          readyState: jsonState.readyState,
          readyStateDesc: getReadyStateDescription(jsonState.readyState)
        });
        appendConsole({
          sender: "Error",
          message: `WebSocket connection not established (${getReadyStateDescription(jsonState.readyState)})`,
        });
      }
    },
    [jsonState.sendJsonMessage, jsonState.readyState, appendConsole]
  );

  return sendJson;
};

function getReadyStateDescription(readyState: number): string {
  switch (readyState) {
    case 0: return "CONNECTING";
    case 1: return "OPEN";
    case 2: return "CLOSING";
    case 3: return "CLOSED";
    default: return "UNINSTANTIATED";
  }
}

export default useSendJSON;