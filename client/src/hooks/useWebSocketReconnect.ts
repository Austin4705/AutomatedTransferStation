import { useCallback } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import useAppendConsole from "./useAppendConsole";
import { ReadyState } from "react-use-websocket";

/**
 * Hook to handle WebSocket reconnection
 * @returns A function to trigger manual reconnection
 */
export const useWebSocketReconnect = () => {
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();
  
  const reconnect = useCallback(() => {
    // Only attempt to reconnect if the socket is closed or in error state
    if (
      jsonState.readyState === ReadyState.CLOSED || 
      jsonState.readyState === ReadyState.CLOSING || 
      jsonState.readyState === ReadyState.UNINSTANTIATED
    ) {
      appendConsole({
        sender: "System",
        message: "Attempting to reconnect WebSocket...",
      });
      
      // Get the actual WebSocket instance if available
      if (jsonState.getWebSocket) {
        const ws = jsonState.getWebSocket();
        
        // If we have a WebSocket instance, close it to trigger reconnection
        if (ws) {
          try {
            ws.close();
            
            // After closing, create a new WebSocket connection
            setTimeout(() => {
              // Create and dispatch a custom event to trigger reconnection
              const reconnectEvent = new CustomEvent('wsReconnect');
              window.dispatchEvent(reconnectEvent);
            }, 500);
          } catch (error) {
            console.error("Error closing WebSocket:", error);
            
            // Fallback to page reload if closing fails
            appendConsole({
              sender: "System",
              message: "Error reconnecting. Reloading page...",
            });
            setTimeout(() => window.location.reload(), 1000);
          }
        } else {
          // If no WebSocket instance, just trigger the reconnect event
          const reconnectEvent = new CustomEvent('wsReconnect');
          window.dispatchEvent(reconnectEvent);
        }
      } else {
        // If no getWebSocket function, fallback to page reload
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