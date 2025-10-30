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
      shouldReconnect: (_closeEvent) => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      retryOnError: true,
      onOpen: () => {
        console.log("WebSocket connection established");
        console.log(`WebSocket connected to ${ws_url}`);
        
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
        const rawMessage = event.data;
        lastRawMessageRef.current = rawMessage;
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
