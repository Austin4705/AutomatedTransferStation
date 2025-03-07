import { useState, useEffect } from "react";
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

  // Request command logs on component mount
  useEffect(() => {
    sendJson({
      type: "REQUEST_LOG_COMMANDS",
    });
    
    // Set up a periodic refresh
    const intervalId = setInterval(() => {
      sendJson({
        type: "REQUEST_LOG_COMMANDS",
      });
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(intervalId);
  }, [sendJson]);

  // Process incoming command logs
  useEffect(() => {
    if (
      jsonState.lastJsonMessage && 
      jsonState.lastJsonMessage.type === "RESPONSE_LOG_COMMANDS" &&
      Array.isArray(jsonState.lastJsonMessage.commands)
    ) {
      const formattedLogs = jsonState.lastJsonMessage.commands.map((cmd: any) => ({
        timestamp: new Date(cmd.timestamp || Date.now()).toLocaleString(),
        command: cmd.command || JSON.stringify(cmd)
      }));
      
      setCommandLogs(formattedLogs);
    }
  }, [jsonState.lastJsonMessage]);

  return (
    <div className="command-log">
      <div className="log-content overflow-auto h-full">
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
          onClick={() => sendJson({ type: "REQUEST_LOG_COMMANDS" })}
          className="refresh-button text-sm"
        >
          Refresh
        </button>
      </div>
    </div>
  );
};

export default CommandLog; 