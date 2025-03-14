import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { PacketManager } from "../packets/PacketHandler";

interface ResponseLogEntry {
  timestamp: string;
  response: string;
}

// Define message types to fix TypeScript errors
interface ResponseMessage {
  type: string;
  message?: string;
  response?: string;
  _loggedByManager?: boolean;
  [key: string]: any;
}

const ResponseLog = () => {
  const [responseLogs, setResponseLogs] = useState<ResponseLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const logContentRef = useRef<HTMLDivElement>(null);
  // Add a ref to track if logs were manually cleared
  const logsManuallyCleared = useRef<boolean>(false);

  // Set up the listener for response logs from PacketManager
  useEffect(() => {
    // Register a listener for response logs
    const unsubscribe = PacketManager.registerResponseLogListener((entry) => {
      if (logsManuallyCleared.current) {
        // If logs were manually cleared, wait a bit before adding new entries
        return;
      }

      const newEntry: ResponseLogEntry = {
        timestamp: new Date(entry.timestamp).toLocaleString(),
        response: entry.message
      };
      
      setResponseLogs(prev => [...prev, newEntry]);
      scrollToBottom();
    });
    
    // Clean up on unmount
    return () => {
      unsubscribe();
    };
  }, []);

  // Process incoming response messages from websocket as a backup
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;
    
    const message = jsonState.lastJsonMessage as ResponseMessage;
    
    // If logs were manually cleared, we need to reset the flag
    // but only process new messages after clearing
    if (logsManuallyCleared.current) {
      return;
    }
    
    // Only handle response-type messages here as a backup
    // Most responses should be handled by the PacketManager listener
    if ((message.type === "RESPONSE" || 
         message.type === "COMMAND_RESULT" || 
         message.type === "ERROR") && 
        !message._loggedByManager) {
        
      const newEntry: ResponseLogEntry = {
        timestamp: new Date().toLocaleString(),
        response: message.message || message.response || JSON.stringify(message)
      };
      
      // Mark as logged to prevent duplicates
      message._loggedByManager = true;
      
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

  // Function to clear logs
  const clearLogs = () => {
    setResponseLogs([]);
    // Mark that logs were manually cleared to prevent immediate re-adding
    logsManuallyCleared.current = true;
    
    // Add a small delay before allowing new messages to be processed
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
          onClick={clearLogs}
          className="clear-button text-sm"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default ResponseLog; 