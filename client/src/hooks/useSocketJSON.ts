import { useEffect, useRef } from "react";
import useWebSocket from "react-use-websocket";
import { useSetRecoilState } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { PacketManager } from "../packets/PacketHandler";

export default function useSocketJSON(ws_url: string) {
  const setJsonState = useSetRecoilState(jsonStateAtom);
  const lastRawMessageRef = useRef<string | null>(null);
  
  const { lastJsonMessage, lastMessage, readyState, sendJsonMessage, getWebSocket } = useWebSocket(
    ws_url,
    {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      shouldReconnect: (_closeEvent) => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      retryOnError: true,
      onOpen: () => {
        console.log("WebSocket connection established");
        console.log(`WebSocket connected to ${ws_url}`);
        
        // Dispatch a custom event that components can listen for
        const wsConnectedEvent = new CustomEvent('wsConnected');
        window.dispatchEvent(wsConnectedEvent);
      },
      onClose: (event) => {
        console.warn("WebSocket connection closed", event);
      },
      onError: (event) => {
        console.error("WebSocket error:", event);
      },
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
      sendJsonMessage: sendJsonMessage,
      getWebSocket: getWebSocket
    });
  }, [lastJsonMessage, readyState, sendJsonMessage, getWebSocket, setJsonState, lastRawMessageRef.current]);
}
