import { useCallback } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import useAppendConsole from "./useAppendConsole";

export const useSendJSON = () => {
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();

  const sendJson = useCallback(
    (data: any) => {
      if (jsonState.sendJsonMessage) {
        // Log the outgoing message to the console
        appendConsole({
          sender: "Client",
          message: JSON.stringify(data),
        });
        
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