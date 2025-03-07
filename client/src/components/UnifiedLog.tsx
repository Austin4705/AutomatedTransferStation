import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";
import { PacketManager } from "../packets/PacketHandler";
import { estimatePacketSize } from "../state/packetTrafficState";

// Maximum number of log entries to keep
const MAX_LOG_ENTRIES = 1000;

interface LogEntry {
  timestamp: string;
  message: string;
  type: "command" | "response" | "outgoing" | "packet";
  rawData?: any; // For storing raw packet data
  size?: number; // For packet size
}

type LogType = "command" | "response" | "outgoing" | "packet";

// Define message types to fix TypeScript errors
interface BaseMessage {
  type: string;
  [key: string]: any;
}

interface CommandMessage extends BaseMessage {
  type: "COMMAND" | "RESPONSE_LOG_COMMANDS";
  command?: string;
  commands?: Array<{timestamp?: number; command?: string}>;
}

interface ResponseMessage extends BaseMessage {
  type: "RESPONSE" | "COMMAND_RESULT" | "ERROR" | "RESPONSE_LOG_RESPONSE";
  message?: string;
  response?: string;
  responses?: Array<{timestamp?: number; response?: string}>;
}

const UnifiedLog = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [visibleLogTypes, setVisibleLogTypes] = useState<Set<LogType>>(new Set(["command", "response", "outgoing", "packet"]));
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);

  // Helper function to add logs while respecting the maximum limit
  const addLogs = (newLogs: LogEntry[], replace = false) => {
    setLogs(prevLogs => {
      // If replacing logs of a specific type, filter out that type first
      const filteredLogs = replace 
        ? prevLogs.filter(log => !newLogs.some(newLog => newLog.type === log.type))
        : prevLogs;
      
      // Combine existing and new logs
      const combinedLogs = [...filteredLogs, ...newLogs];
      
      // Trim to maximum size if needed
      return combinedLogs.length > MAX_LOG_ENTRIES 
        ? combinedLogs.slice(combinedLogs.length - MAX_LOG_ENTRIES) 
        : combinedLogs;
    });
  };

  // Register packet traffic listener
  useEffect(() => {
    const unsubscribe = PacketManager.registerTrafficListener((packetInfo) => {
      // Get the raw string representation of the entire packet
      const rawPacket = JSON.stringify({
        type: packetInfo.type,
        data: packetInfo.data
      });
      
      const newEntry: LogEntry = {
        timestamp: new Date(packetInfo.timestamp).toLocaleString(),
        message: rawPacket,
        type: "packet",
        rawData: packetInfo.data,
        size: packetInfo.size
      };
      
      addLogs([newEntry]);
      scrollToBottom();
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Process incoming messages for command logs
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as BaseMessage;
    
    // Handle bulk command logs
    if (message.type === "RESPONSE_LOG_COMMANDS" && Array.isArray((message as CommandMessage).commands)) {
      const cmdMessage = message as CommandMessage;
      const formattedLogs = cmdMessage.commands!.map((cmd: any) => ({
        timestamp: new Date(cmd.timestamp || Date.now()).toLocaleString(),
        message: cmd.command || JSON.stringify(cmd),
        type: "command" as const
      }));
      
      // Replace existing command logs with new ones
      addLogs(formattedLogs, true);
      scrollToBottom();
    }
    
    // Handle individual command
    else if (message.type === "COMMAND") {
      const cmdMessage = message as CommandMessage;
      const newEntry: LogEntry = {
        timestamp: new Date().toLocaleString(),
        message: cmdMessage.command || JSON.stringify(message),
        type: "command"
      };
      
      addLogs([newEntry]);
      scrollToBottom();
    }
    
    // Handle bulk response logs
    else if (message.type === "RESPONSE_LOG_RESPONSE" && Array.isArray((message as ResponseMessage).responses)) {
      const respMessage = message as ResponseMessage;
      const formattedLogs = respMessage.responses!.map((resp: any) => ({
        timestamp: new Date(resp.timestamp || Date.now()).toLocaleString(),
        message: resp.response || JSON.stringify(resp),
        type: "response" as const
      }));
      
      // Replace existing response logs with new ones
      addLogs(formattedLogs, true);
      scrollToBottom();
    }
    
    // Handle individual responses
    else if (
      message.type === "RESPONSE" || 
      message.type === "COMMAND_RESULT" || 
      message.type === "ERROR"
    ) {
      const respMessage = message as ResponseMessage;
      const newEntry: LogEntry = {
        timestamp: new Date().toLocaleString(),
        message: respMessage.message || respMessage.response || JSON.stringify(message),
        type: "response"
      };
      
      addLogs([newEntry]);
      scrollToBottom();
    }
  }, [jsonState.lastJsonMessage]);

  // Track outgoing messages
  useEffect(() => {
    const handleOutgoingMessage = (event: CustomEvent) => {
      const message = event.detail;
      const newEntry: LogEntry = {
        timestamp: new Date().toLocaleString(),
        message: typeof message === 'string' ? message : JSON.stringify(message),
        type: "outgoing"
      };
      
      addLogs([newEntry]);
      scrollToBottom();
    };

    window.addEventListener('outgoingMessage' as any, handleOutgoingMessage);
    
    return () => {
      window.removeEventListener('outgoingMessage' as any, handleOutgoingMessage);
    };
  }, []);

  const scrollToBottom = () => {
    setTimeout(() => {
      if (logContentRef.current) {
        logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
      }
    }, 100);
  };

  // Function to request command logs
  const requestCommandLogs = () => {
    sendJson({
      type: "REQUEST_LOG_COMMANDS",
    });
  };

  // Function to request response logs
  const requestResponseLogs = () => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
  };

  // Toggle log type visibility
  const toggleLogType = (type: LogType) => {
    setVisibleLogTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(type)) {
        newSet.delete(type);
      } else {
        newSet.add(type);
      }
      return newSet;
    });
  };

  // Filter logs based on visible types
  const filteredLogs = logs.filter(log => visibleLogTypes.has(log.type));

  // Get color for log type
  const getLogTypeColor = (type: "command" | "response" | "outgoing" | "packet") => {
    switch (type) {
      case "command":
        return "#3498db"; // Blue
      case "response":
        return "#2ecc71"; // Green
      case "outgoing":
        return "#e67e22"; // Orange
      case "packet":
        return "#9b59b6"; // Purple
      default:
        return "#718096"; // Gray
    }
  };

  // Add a dedicated clear function
  const clearLogs = () => {
    setLogs([]); // Directly set logs to an empty array
  };

  return (
    <div className="unified-log h-full flex flex-col">
      <div className="log-controls p-2 bg-gray-100 rounded mb-2">
        <div className="flex items-center justify-between mb-2">
          <div className="flex gap-2">
            <button 
              onClick={requestCommandLogs}
              className="refresh-button text-sm bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded"
            >
              Refresh Commands
            </button>
            
            <button 
              onClick={requestResponseLogs}
              className="refresh-button text-sm bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded"
            >
              Refresh Responses
            </button>
            
            <button 
              onClick={clearLogs}
              className="clear-button text-sm bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded"
            >
              Clear
            </button>
          </div>

        </div>
        
        <div className="log-type-filters flex flex-wrap items-center gap-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="command-logs"
              checked={visibleLogTypes.has("command")}
              onChange={() => toggleLogType("command")}
              className="mr-1"
            />
            <label htmlFor="command-logs" className="text-sm cursor-pointer flex items-center">
              <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("command") }}></span>
              Commands
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="response-logs"
              checked={visibleLogTypes.has("response")}
              onChange={() => toggleLogType("response")}
              className="mr-1"
            />
            <label htmlFor="response-logs" className="text-sm cursor-pointer flex items-center">
              <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("response") }}></span>
              Responses
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="outgoing-logs"
              checked={visibleLogTypes.has("outgoing")}
              onChange={() => toggleLogType("outgoing")}
              className="mr-1"
            />
            <label htmlFor="outgoing-logs" className="text-sm cursor-pointer flex items-center">
              <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("outgoing") }}></span>
              Outgoing
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="packet-logs"
              checked={visibleLogTypes.has("packet")}
              onChange={() => toggleLogType("packet")}
              className="mr-1"
            />
            <label htmlFor="packet-logs" className="text-sm cursor-pointer flex items-center">
              <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("packet") }}></span>
              Packets
            </label>
          </div>
        </div>
      </div>
      
      <div className="flex-grow flex flex-col border border-gray-200 rounded overflow-hidden">
        <div 
          ref={logContentRef}
          className="log-content flex-grow overflow-auto"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-gray-600 text-sm p-4 text-center">No logs available</div>
          ) : (
            <ul className="log-list m-0 p-0" style={{ listStyle: "none" }}>
              {filteredLogs.map((log, index) => (
                <li 
                  key={index} 
                  className="log-item p-2 text-sm border-b border-gray-100 hover:bg-gray-50"
                  style={{ borderLeftWidth: "4px", borderLeftStyle: "solid", borderLeftColor: getLogTypeColor(log.type) }}
                >
                  <div className="flex items-center">
                    <span className="log-type text-xs font-medium mr-2 px-1 py-0.5 rounded" style={{ 
                      backgroundColor: getLogTypeColor(log.type),
                      color: "white"
                    }}>
                      {log.type.toUpperCase()}
                    </span>
                    <span className="log-timestamp text-gray-600">[{log.timestamp}]</span>
                    {log.size && (
                      <span className="log-size text-xs ml-2 text-gray-500">
                        ({log.size} bytes)
                      </span>
                    )}
                  </div>
                  <div className="log-message mt-1 pl-2 font-mono text-xs overflow-x-auto">
                    {log.message}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <div className="text-xs text-gray-500 p-2 text-right bg-gray-50 border-t border-gray-200 flex-shrink-0">
          Showing {filteredLogs.length} of {logs.length} logs (max: {MAX_LOG_ENTRIES})
        </div>
      </div>
    </div>
  );
};

export default UnifiedLog; 