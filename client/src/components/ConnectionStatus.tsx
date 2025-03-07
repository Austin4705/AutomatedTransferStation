import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { ReadyState } from "react-use-websocket";

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

  return (
    <div className="connection-status">
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
        </span>
      </div>
    </div>
  );
};

export default ConnectionStatus; 