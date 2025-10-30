import { useCallback } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import useAppendConsole from "./useAppendConsole";
import { ReadyState } from "react-use-websocket";

export const useWebSocketReconnect = () => {
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();
  
  const reconnect = useCallback(() => {
    if (
      jsonState.readyState === ReadyState.CLOSED || 
      jsonState.readyState === ReadyState.CLOSING || 
      jsonState.readyState === ReadyState.UNINSTANTIATED
    ) {
      appendConsole({
        sender: "System",
        message: "Attempting to reconnect WebSocket...",
      });
      
      if (jsonState.getWebSocket) {
        const ws = jsonState.getWebSocket();
        
        if (ws) {
          try {
            ws.close();
            
            setTimeout(() => {
              const reconnectEvent = new CustomEvent('wsReconnect');
              window.dispatchEvent(reconnectEvent);
            }, 500);
          } catch (error) {
            console.error("Error closing WebSocket:", error);
            
            appendConsole({
              sender: "System",
              message: "Error reconnecting. Reloading page...",
            });
            setTimeout(() => window.location.reload(), 1000);
          }
        } else {
          const reconnectEvent = new CustomEvent('wsReconnect');
          window.dispatchEvent(reconnectEvent);
        }
      } else {
        appendConsole({
          sender: "System",
          message: "No WebSocket instance available. Reloading page...",
        });
        setTimeout(() => window.location.reload(), 1000);
      }
      
      return true;
    } else {
      appendConsole({
        sender: "System",
        message: "WebSocket is already connected or connecting.",
      });
      return false;
    }
  }, [jsonState, appendConsole]);
  
  return reconnect;
};

export default useWebSocketReconnect; 