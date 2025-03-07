import { useEffect, useRef } from "react";
import useWebSocket from "react-use-websocket";
import { useSetRecoilState } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { PacketManager } from "../packets/PacketHandler";

export default function useSocketJSON(ws_url: string) {
  const setJsonState = useSetRecoilState(jsonStateAtom);
  const lastRawMessageRef = useRef<string | null>(null);
  
  const { lastJsonMessage, lastMessage, readyState, sendJsonMessage } = useWebSocket(
    ws_url,
    {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      shouldReconnect: (_closeEvent) => true,
      onMessage: (event) => {
        // Store the raw message string
        const rawMessage = event.data;
        lastRawMessageRef.current = rawMessage;
        
        // Set the raw message in the PacketManager
        PacketManager.setLastRawMessage(rawMessage);
      }
    }
  );

  useEffect(() => {
    setJsonState({
      lastJsonMessage: lastJsonMessage,
      lastRawMessage: lastRawMessageRef.current,
      readyState: readyState,
      sendJsonMessage: sendJsonMessage
    });
  }, [lastJsonMessage, readyState, sendJsonMessage, setJsonState, lastRawMessageRef.current]);
}
