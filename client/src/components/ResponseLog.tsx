import { useState, useEffect, useRef } from "react";
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
  const logContentRef = useRef<HTMLDivElement>(null);

  // Process incoming messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage;
    
    // Handle bulk response logs
    if (message.type === "RESPONSE_LOG_RESPONSE" && Array.isArray(message.responses)) {
      const formattedLogs = message.responses.map((resp: any) => ({
        timestamp: new Date(resp.timestamp || Date.now()).toLocaleString(),
        response: resp.response || JSON.stringify(resp)
      }));
      
      setResponseLogs(formattedLogs);
      
      // Scroll to bottom after update
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    }
    
    // Handle individual responses
    else if (
      message.type === "RESPONSE" || 
      message.type === "COMMAND_RESULT" || 
      message.type === "ERROR"
    ) {
      const newEntry: ResponseLogEntry = {
        timestamp: new Date().toLocaleString(),
        response: message.message || message.response || JSON.stringify(message)
      };
      
      setResponseLogs(prev => [...prev, newEntry]);
      
      // Scroll to bottom after update
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [jsonState.lastJsonMessage]);

  // Function to request response logs
  const requestResponseLogs = () => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
  };

  return (
    <div className="response-log h-full flex flex-col">
      <div 
        ref={logContentRef}
        className="log-content flex-grow overflow-auto"
      >
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
          onClick={requestResponseLogs}
          className="refresh-button text-sm"
        >
          Refresh
        </button>
        <button 
          onClick={() => setResponseLogs([])}
          className="clear-button text-sm ml-2"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default ResponseLog; 