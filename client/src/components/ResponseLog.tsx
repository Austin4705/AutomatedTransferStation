import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";

interface ResponseLogEntry {
  timestamp: string;
  response: string;
}

// Define message types to fix TypeScript errors
interface ResponseMessage {
  type: string;
  message?: string;
  response?: string;
  responses?: Array<{timestamp?: number; response?: string}>;
  [key: string]: any;
}

const ResponseLog = () => {
  const [responseLogs, setResponseLogs] = useState<ResponseLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);
  // Add a ref to track the last processed message to avoid duplicates
  const lastProcessedMessageRef = useRef<any>(null);
  // Add a ref to track if logs were manually cleared
  const logsManuallyCleared = useRef<boolean>(false);

  // Process incoming messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    // Skip if this is the same message we already processed
    if (lastProcessedMessageRef.current === jsonState.lastJsonMessage) {
      return;
    }

    // Update the last processed message
    lastProcessedMessageRef.current = jsonState.lastJsonMessage;
    
    const message = jsonState.lastJsonMessage as ResponseMessage;
    
    // If logs were manually cleared, we need to reset the flag
    // but only process new messages after clearing
    if (logsManuallyCleared.current) {
      logsManuallyCleared.current = false;
      // Only process this message if it's new (arrived after clearing)
      const currentTime = new Date().getTime();
      const messageTime = message.timestamp ? new Date(message.timestamp).getTime() : currentTime;
      // If the message is older than when we cleared, skip it
      if (messageTime < currentTime - 1000) { // 1 second buffer
        return;
      }
    }
    
    // Handle bulk response logs
    if (message.type === "RESPONSE_LOG_RESPONSE" && Array.isArray(message.responses)) {
      const formattedLogs = message.responses.map((resp: any) => ({
        timestamp: new Date(resp.timestamp || Date.now()).toLocaleString(),
        response: resp.response || JSON.stringify(resp)
      }));
      
      setResponseLogs(formattedLogs);
      
      scrollToBottom();
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
      
      scrollToBottom();
    }
  }, [jsonState.lastJsonMessage]);

  // Listen for logs-cleared event from UnifiedLog
  useEffect(() => {
    const handleLogsClearedEvent = (event: Event) => {
      clearLogs();
    };
    
    // Add event listener
    document.addEventListener('logs-cleared', handleLogsClearedEvent as EventListener);
    
    // Clean up
    return () => {
      document.removeEventListener('logs-cleared', handleLogsClearedEvent as EventListener);
    };
  }, []);

  // Function to scroll to bottom
  const scrollToBottom = () => {
    if (logContentRef.current) {
      logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
    }
  };

  // Function to request response logs
  const requestResponseLogs = () => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
  };

  // Function to clear logs
  const clearLogs = () => {
    setResponseLogs([]);
    // Mark that logs were manually cleared to prevent immediate re-adding
    logsManuallyCleared.current = true;
    // Reset the last processed message to allow new messages to come in
    // Setting to null isn't enough - we need to completely reset the reference
    lastProcessedMessageRef.current = undefined;
    
    // Add a small delay before allowing new messages to be processed
    // This helps prevent the last message from being immediately re-added
    setTimeout(() => {
      logsManuallyCleared.current = false;
    }, 100);
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
          onClick={clearLogs}
          className="clear-button text-sm ml-2"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default ResponseLog; 