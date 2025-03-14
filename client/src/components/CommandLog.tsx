import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { PacketManager } from "../packets/PacketHandler";

interface CommandLogEntry {
  timestamp: string;
  command: string;
}

// Define message types to fix TypeScript errors
interface CommandMessage {
  type: string;
  command?: string;
  _loggedByManager?: boolean;
  [key: string]: any;
}

const CommandLog = () => {
  const [commandLogs, setCommandLogs] = useState<CommandLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const logContentRef = useRef<HTMLDivElement>(null);
  // Add a ref to track if logs were manually cleared
  const logsManuallyCleared = useRef<boolean>(false);

  // Set up the listener for command logs from PacketManager
  useEffect(() => {
    // Register a listener for command logs
    const unsubscribe = PacketManager.registerCommandLogListener((entry) => {
      if (logsManuallyCleared.current) {
        // If logs were manually cleared, wait a bit before adding new entries
        return;
      }

      const newEntry: CommandLogEntry = {
        timestamp: new Date(entry.timestamp).toLocaleString(),
        command: entry.message
      };
      
      setCommandLogs(prev => [...prev, newEntry]);
      scrollToBottom();
    });
    
    // Clean up on unmount
    return () => {
      unsubscribe();
    };
  }, []);

  // Process incoming COMMAND messages from websocket as a backup
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;
    
    const message = jsonState.lastJsonMessage as CommandMessage;
    
    // If logs were manually cleared, we need to reset the flag
    // but only process new messages after clearing
    if (logsManuallyCleared.current) {
      return;
    }
    
    // Only handle COMMAND messages here as a backup
    // Most commands should be handled by the PacketManager listener
    if (message.type === "COMMAND" && !message._loggedByManager) {
      const newEntry: CommandLogEntry = {
        timestamp: new Date().toLocaleString(),
        command: message.command || JSON.stringify(message)
      };
      
      // Mark as logged to prevent duplicates
      message._loggedByManager = true;
      
      setCommandLogs(prev => [...prev, newEntry]);
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
    setCommandLogs([]);
    // Mark that logs were manually cleared to prevent immediate re-adding
    logsManuallyCleared.current = true;
    
    // Add a small delay before allowing new messages to be processed
    setTimeout(() => {
      logsManuallyCleared.current = false;
    }, 100);
  };

  return (
    <div className="command-log h-full flex flex-col">
      <div 
        ref={logContentRef}
        className="log-content flex-grow overflow-auto"
      >
        {commandLogs.length === 0 ? (
          <div className="text-gray-600 text-sm p-2">No command logs available</div>
        ) : (
          <ul className="log-list m-0 p-0" style={{ listStyle: "none" }}>
            {commandLogs.map((log, index) => (
              <li key={index} className="log-item p-2 text-sm border-b border-gray-100">
                <span className="log-timestamp text-gray-600">[{log.timestamp}]</span>{" "}
                <span className="log-message">{log.command}</span>
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

export default CommandLog; 