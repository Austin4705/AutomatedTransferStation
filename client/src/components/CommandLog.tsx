import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";

interface CommandLogEntry {
  timestamp: string;
  command: string;
}

const CommandLog = () => {
  const [commandLogs, setCommandLogs] = useState<CommandLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);

  // Remove the automatic request on component mount
  // We'll only request logs when the user clicks the Refresh button

  // Process incoming messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage;
    
    // Handle bulk command logs
    if (message.type === "RESPONSE_LOG_COMMANDS" && Array.isArray(message.commands)) {
      const formattedLogs = message.commands.map((cmd: any) => ({
        timestamp: new Date(cmd.timestamp || Date.now()).toLocaleString(),
        command: cmd.command || JSON.stringify(cmd)
      }));
      
      setCommandLogs(formattedLogs);
      
      // Scroll to bottom after update
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    }
    
    // Handle individual command
    else if (message.type === "COMMAND") {
      const newEntry: CommandLogEntry = {
        timestamp: new Date().toLocaleString(),
        command: message.command || JSON.stringify(message)
      };
      
      setCommandLogs(prev => [...prev, newEntry]);
      
      // Scroll to bottom after update
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [jsonState.lastJsonMessage]);

  // Function to request command logs
  const requestCommandLogs = () => {
    sendJson({
      type: "REQUEST_LOG_COMMANDS",
    });
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
          onClick={requestCommandLogs}
          className="refresh-button text-sm"
        >
          Refresh
        </button>
        <button 
          onClick={() => setCommandLogs([])}
          className="clear-button text-sm ml-2"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default CommandLog; 