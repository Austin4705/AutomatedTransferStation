import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { ReadyState } from "react-use-websocket";
import useWebSocketReconnect from "../../hooks/useWebSocketReconnect";
import { useEffect, useState } from "react";

const readyStateMap = {
  [ReadyState.CONNECTING]: "Connecting",
  [ReadyState.OPEN]: "Connected",
  [ReadyState.CLOSING]: "Closing",
  [ReadyState.CLOSED]: "Disconnected",
  [ReadyState.UNINSTANTIATED]: "Uninstantiated",
};

const statusColorMap = {
  [ReadyState.CONNECTING]: "#f39c12", // Yellow
  [ReadyState.OPEN]: "#2ecc71", // Green
  [ReadyState.CLOSING]: "#e74c3c", // Red
  [ReadyState.CLOSED]: "#e74c3c", // Red
  [ReadyState.UNINSTANTIATED]: "#95a5a6", // Gray
};

const ConnectionStatus = () => {
  const jsonState = useRecoilValue(jsonStateAtom);
  const readyState = jsonState.readyState;
  const reconnect = useWebSocketReconnect();
  
  const [connectingTime, setConnectingTime] = useState(0);
  const [connectingTimer, setConnectingTimer] = useState<ReturnType<typeof setInterval> | null>(null);
  
  useEffect(() => {
    if (readyState === ReadyState.CONNECTING) {
      if (!connectingTimer) {
        const timer = setInterval(() => {
          setConnectingTime(prev => prev + 1);
        }, 1000);
        setConnectingTimer(timer);
      }
    } else {
      if (connectingTimer) {
        clearInterval(connectingTimer);
        setConnectingTimer(null);
      }
      setConnectingTime(0);
    }
    
    return () => {
      if (connectingTimer) {
        clearInterval(connectingTimer);
      }
    };
  }, [readyState, connectingTimer]);
  
  const shouldShowReconnectButton = 
    readyState === ReadyState.CLOSED || 
    readyState === ReadyState.UNINSTANTIATED ||
    readyState === ReadyState.CLOSING ||
    (readyState === ReadyState.CONNECTING && connectingTime > 5);

  return (
    <div className="connection-status flex items-center">
      {shouldShowReconnectButton && (
        <button 
          className="reconnect-button mr-3 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
          onClick={reconnect}
          title="Reconnect WebSocket"
        >
          Reconnect
        </button>
      )}
      <div className="status-indicator">
        <span 
          className="status-dot"
          style={{ 
            backgroundColor: statusColorMap[readyState],
            display: "inline-block",
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            marginRight: "8px"
          }}
        />
        <span className="status-text">
          {readyStateMap[readyState]}
          {readyState === ReadyState.CONNECTING && connectingTime > 0 && ` (${connectingTime}s)`}
        </span>
      </div>
    </div>
  );
};

export default ConnectionStatus; 