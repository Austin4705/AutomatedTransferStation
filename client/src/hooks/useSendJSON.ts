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
        // Check if packet definitions have been loaded
        if (PacketManager.isInitialized && !PacketManager.isInitialized()) {
          console.warn("Packet manager not initialized yet. Initializing now...");
          PacketManager.initialize().then(() => {
            console.log("Packet manager initialized from useSendJSON");
          });
        }

        // Log the outgoing message to the console
        appendConsole({
          sender: "Client",
          message: JSON.stringify(data),
        });
        
        // Dispatch a custom event for the OutgoingLog component
        const outgoingEvent = new CustomEvent('outgoingMessage', { 
          detail: data 
        });
        window.dispatchEvent(outgoingEvent);
        
        // Send the message
        jsonState.sendJsonMessage(data);
      } else {
        console.error("WebSocket connection not established");
        appendConsole({
          sender: "Error",
          message: "WebSocket connection not established",
        });
      }
    },
    [jsonState.sendJsonMessage, appendConsole]
  );

  return sendJson;
};

export default useSendJSON;