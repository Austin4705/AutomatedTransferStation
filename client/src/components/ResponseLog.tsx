import { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";

interface ResponseLogEntry {
  timestamp: string;
  response: string;
}

const ResponseLog = () => {
  const [responseLogs, setResponseLogs] = useState<ResponseLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Request response logs on component mount
  useEffect(() => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
    
    // Set up a periodic refresh
    const intervalId = setInterval(() => {
      sendJson({
        type: "REQUEST_LOG_RESPONSE",
      });
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [sendJson]);

  // Process incoming response logs
  useEffect(() => {
    if (
      jsonState.lastJsonMessage && 
      jsonState.lastJsonMessage.type === "RESPONSE_LOG_RESPONSE" &&
      Array.isArray(jsonState.lastJsonMessage.responses)
    ) {
      const formattedLogs = jsonState.lastJsonMessage.responses.map((resp: any) => ({
        timestamp: new Date(resp.timestamp || Date.now()).toLocaleString(),
        response: resp.response || JSON.stringify(resp)
      }));
      
      setResponseLogs(formattedLogs);
    }
  }, [jsonState.lastJsonMessage]);

  return (
    <div className="response-log">
      <div className="log-content overflow-auto h-full">
        {responseLogs.length === 0 ? (
          <div className="text-gray-600 text-sm p-2">No response logs available</div>
        ) : (
          <ul className="log-list m-0 p-0" style={{ listStyle: "none" }}>
            {responseLogs.map((log, index) => (
              <li key={index} className="log-item p-2 text-sm border-b border-gray-100">
                <span className="log-timestamp text-gray-600">[{log.timestamp}]</span>{" "}
                <span className="log-message">{log.response}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="log-actions mt-2">
        <button 
          onClick={() => sendJson({ type: "REQUEST_LOG_RESPONSE" })}
          className="refresh-button text-sm"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};

export default ResponseLog; 