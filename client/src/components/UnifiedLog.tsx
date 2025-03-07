import { useState, useEffect, useRef, useMemo } from "react";
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
  packetType?: string; // For packet type filtering
  isUnknown?: boolean; // For unknown packets
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

// Common packet types that might not be in definitions
const COMMON_PACKET_TYPES: string[] = [];
// ["COMMAND", "REQUEST_POSITION", "SEND_COMMAND", "TRACE_OVER", "SNAP_SHOT", "REQUEST_LOG_COMMANDS", "REQUEST_LOG_RESPONSE"];

// Common outgoing message types
const COMMON_OUTGOING_TYPES: string[] = [];
// ["COMMAND", "REQUEST_POSITION", "SEND_COMMAND", "TRACE_OVER", "SNAP_SHOT", "REQUEST_LOG_COMMANDS", "REQUEST_LOG_RESPONSE"];

const UnifiedLog = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [visibleLogTypes, setVisibleLogTypes] = useState<Set<LogType>>(new Set(["command", "response", "outgoing", "packet"]));
  const [showUnknownPackets, setShowUnknownPackets] = useState<boolean>(true);
  const [showUnknownOutgoing, setShowUnknownOutgoing] = useState<boolean>(true);
  const [selectedPacketTypes, setSelectedPacketTypes] = useState<Set<string>>(new Set());
  const [selectedOutgoingTypes, setSelectedOutgoingTypes] = useState<Set<string>>(new Set());
  const [definedPacketTypes, setDefinedPacketTypes] = useState<string[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);
  const packetDefsLoaded = useRef<boolean>(false);

  // Load packet definitions from document
  useEffect(() => {
    const loadPacketDefinitions = async () => {
      if (packetDefsLoaded.current) return;
      
      try {
        // Load packet definitions from the shared directory
        const response = await fetch('/shared/packet_definitions.json');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const packetDefs = await response.json();
        
        // Extract packet types from definitions
        const packetTypes = Object.keys(packetDefs.packets || {});
        
        // Combine with common packet types
        const allPacketTypes = [...new Set([...packetTypes, ...COMMON_PACKET_TYPES])].sort();
        
        setDefinedPacketTypes(allPacketTypes);
        
        // Initialize all packet types as selected
        setSelectedPacketTypes(new Set(allPacketTypes));
        
        // Initialize all outgoing types as selected
        setSelectedOutgoingTypes(new Set(COMMON_OUTGOING_TYPES));
        
        packetDefsLoaded.current = true;
        
        console.log("Loaded packet types from definitions:", allPacketTypes);
      } catch (error) {
        console.error('Failed to load packet definitions:', error);
        // Fallback to common packet types
        setDefinedPacketTypes(COMMON_PACKET_TYPES);
        
        // Initialize all packet types as selected
        setSelectedPacketTypes(new Set(COMMON_PACKET_TYPES));
        
        // Initialize all outgoing types as selected
        setSelectedOutgoingTypes(new Set(COMMON_OUTGOING_TYPES));
        
        packetDefsLoaded.current = true;
      }
    };
    
    loadPacketDefinitions();
  }, []);

  // Extract unique packet types from logs and combine with defined types
  const packetTypes = useMemo(() => {
    const typesFromLogs = new Set<string>();
    logs.forEach(log => {
      if (log.type === "packet" && log.packetType) {
        typesFromLogs.add(log.packetType);
      }
    });
    
    // Combine with defined packet types
    const allTypes = new Set([...definedPacketTypes, ...typesFromLogs]);
    return Array.from(allTypes).sort();
  }, [logs, definedPacketTypes]);

  // Extract unique outgoing message types from logs and combine with common types
  const outgoingTypes = useMemo(() => {
    const typesFromLogs = new Set<string>();
    logs.forEach(log => {
      if (log.type === "outgoing" && log.packetType) {
        typesFromLogs.add(log.packetType);
      }
    });
    
    // Combine with common outgoing types
    const allTypes = new Set([...COMMON_OUTGOING_TYPES, ...typesFromLogs]);
    return Array.from(allTypes).sort();
  }, [logs]);

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

  // Toggle packet type selection
  const togglePacketType = (type: string) => {
    setSelectedPacketTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(type)) {
        newSet.delete(type);
      } else {
        newSet.add(type);
      }
      return newSet;
    });
  };

  // Toggle outgoing type selection
  const toggleOutgoingType = (type: string) => {
    setSelectedOutgoingTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(type)) {
        newSet.delete(type);
      } else {
        newSet.add(type);
      }
      return newSet;
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
      
      // Determine if this is an unknown packet type
      const isUnknown = !PacketManager.isKnownPacketType(packetInfo.type);
      
      const newEntry: LogEntry = {
        timestamp: new Date(packetInfo.timestamp).toLocaleString(),
        message: rawPacket,
        type: "packet",
        rawData: packetInfo.data,
        size: packetInfo.size,
        packetType: packetInfo.type,
        isUnknown
      };
      
      // Add the new entry immediately to the logs
      setLogs(prevLogs => {
        const newLogs = [...prevLogs, newEntry];
        // Trim to maximum size if needed
        return newLogs.length > MAX_LOG_ENTRIES 
          ? newLogs.slice(newLogs.length - MAX_LOG_ENTRIES) 
          : newLogs;
      });
      
      // Scroll to bottom to show the new entry
      scrollToBottom();
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Track outgoing messages
  useEffect(() => {
    const handleOutgoingMessage = (event: CustomEvent) => {
      const message = event.detail;
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      
      // Try to extract type from JSON if possible
      let messageType = "";
      let isUnknown = false;
      
      try {
        if (typeof message === 'object' && message.type) {
          messageType = message.type;
          // Check if this is an unknown packet type
          isUnknown = !COMMON_OUTGOING_TYPES.includes(messageType) && 
                      !definedPacketTypes.includes(messageType);
        } else if (typeof message === 'string') {
          try {
            const parsed = JSON.parse(message);
            if (parsed && parsed.type) {
              messageType = parsed.type;
              // Check if this is an unknown packet type
              isUnknown = !COMMON_OUTGOING_TYPES.includes(messageType) && 
                          !definedPacketTypes.includes(messageType);
            }
          } catch {
            // If we can't parse the string, consider it unknown
            isUnknown = true;
          }
        }
      } catch (e) {
        // Ignore parsing errors
        isUnknown = true;
      }
      
      const newEntry: LogEntry = {
        timestamp: new Date().toLocaleString(),
        message: messageStr,
        type: "outgoing",
        packetType: messageType,
        isUnknown
      };
      
      // Add the new entry immediately to the logs
      setLogs(prevLogs => {
        const newLogs = [...prevLogs, newEntry];
        // Trim to maximum size if needed
        return newLogs.length > MAX_LOG_ENTRIES 
          ? newLogs.slice(newLogs.length - MAX_LOG_ENTRIES) 
          : newLogs;
      });
      
      // Scroll to bottom to show the new entry
      scrollToBottom();
    };

    window.addEventListener('outgoingMessage' as any, handleOutgoingMessage);
    
    return () => {
      window.removeEventListener('outgoingMessage' as any, handleOutgoingMessage);
    };
  }, [definedPacketTypes]);

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

  // Filter logs based on visible types and filters
  const filteredLogs = logs.filter(log => {
    // First filter by log type - if the checkbox is unchecked, don't show any data of that type
    if (!visibleLogTypes.has(log.type)) return false;
    
    // Filter packet logs
    if (log.type === "packet") {
      // If it's an unknown packet, check the unknown packets checkbox
      if (log.isUnknown) return showUnknownPackets;
      
      // Otherwise, check if this packet type is selected
      return log.packetType ? selectedPacketTypes.has(log.packetType) : false;
    }
    
    // Filter outgoing messages
    if (log.type === "outgoing") {
      // If it's an unknown outgoing message, check the unknown outgoing checkbox
      if (log.isUnknown) return showUnknownOutgoing;
      
      // Otherwise, check if this outgoing type is selected
      return log.packetType ? selectedOutgoingTypes.has(log.packetType) : false;
    }
    
    // For command and response logs, just show them if their type is visible
    return true;
  });

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

  // Add click handler to close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const outgoingFilterElem = document.getElementById('outgoing-filter-options');
      const packetFilterElem = document.getElementById('packet-filter-options');
      
      // Check if the click was outside the outgoing filter dropdown
      if (outgoingFilterElem && !outgoingFilterElem.classList.contains('hidden')) {
        const outgoingButton = document.querySelector('[data-dropdown="outgoing"]');
        if (
          !outgoingFilterElem.contains(event.target as Node) && 
          (!outgoingButton || !outgoingButton.contains(event.target as Node))
        ) {
          outgoingFilterElem.classList.add('hidden');
        }
      }
      
      // Check if the click was outside the packet filter dropdown
      if (packetFilterElem && !packetFilterElem.classList.contains('hidden')) {
        const packetButton = document.querySelector('[data-dropdown="packet"]');
        if (
          !packetFilterElem.contains(event.target as Node) && 
          (!packetButton || !packetButton.contains(event.target as Node))
        ) {
          packetFilterElem.classList.add('hidden');
        }
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="unified-log h-full flex flex-col">
      <div className="log-controls p-2 bg-gray-100 rounded mb-2 overflow-visible">
        {/* Log type filters - 4 rows with checkboxes */}
        <div className="log-type-filters flex flex-col gap-2 mb-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="command-logs"
              checked={visibleLogTypes.has("command")}
              onChange={() => toggleLogType("command")}
              className="mr-2"
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
              className="mr-2"
            />
            <label htmlFor="response-logs" className="text-sm cursor-pointer flex items-center">
              <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("response") }}></span>
              Responses
            </label>
          </div>
          
          {/* Outgoing logs with collapsible filter section */}
          <div className="flex flex-col">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="outgoing-logs"
                checked={visibleLogTypes.has("outgoing")}
                onChange={() => toggleLogType("outgoing")}
                className="mr-2"
              />
              <label htmlFor="outgoing-logs" className="text-sm cursor-pointer flex items-center">
                <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("outgoing") }}></span>
                Outgoing
              </label>
              
              {/* Collapsible button for outgoing filter options */}
              {visibleLogTypes.has("outgoing") && (
                <button 
                  data-dropdown="outgoing"
                  onClick={() => {
                    const outgoingFilterElem = document.getElementById('outgoing-filter-options');
                    if (outgoingFilterElem) {
                      outgoingFilterElem.classList.toggle('hidden');
                      
                      // Close the other dropdown if open
                      const packetFilterElem = document.getElementById('packet-filter-options');
                      if (packetFilterElem && !packetFilterElem.classList.contains('hidden')) {
                        packetFilterElem.classList.add('hidden');
                      }
                    }
                  }}
                  className="ml-4 text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded flex items-center"
                >
                  Filter Options
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              )}
            </div>
            
            {/* Collapsible outgoing filter options */}
            {visibleLogTypes.has("outgoing") && (
              <div id="outgoing-filter-options" className="hidden ml-6 mt-2 p-2 bg-gray-50 rounded border border-gray-200 z-10 absolute shadow-md">
                {outgoingTypes.length > 0 && (
                  <div className="mt-2">
                    <div className="text-sm font-medium mb-1">Filter by Type:</div>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1 thin-scrollbar">
                      {outgoingTypes.map(type => (
                        <div key={type} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`outgoing-type-${type}`}
                            checked={selectedOutgoingTypes.has(type)}
                            onChange={() => toggleOutgoingType(type)}
                            className="mr-1"
                          />
                          <label htmlFor={`outgoing-type-${type}`} className="text-sm cursor-pointer truncate">
                            {type}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="mt-3 border-t border-gray-200 pt-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="unknown-outgoing"
                      checked={showUnknownOutgoing}
                      onChange={() => setShowUnknownOutgoing(!showUnknownOutgoing)}
                      className="mr-1"
                    />
                    <label htmlFor="unknown-outgoing" className="text-sm cursor-pointer">
                      Unknown Outgoing
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Packet logs with collapsible filter section */}
          <div className="flex flex-col">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="packet-logs"
                checked={visibleLogTypes.has("packet")}
                onChange={() => toggleLogType("packet")}
                className="mr-2"
              />
              <label htmlFor="packet-logs" className="text-sm cursor-pointer flex items-center">
                <span className="w-3 h-3 inline-block mr-1 rounded-sm" style={{ backgroundColor: getLogTypeColor("packet") }}></span>
                Packets
              </label>
              
              {/* Collapsible button for packet filter options */}
              {visibleLogTypes.has("packet") && (
                <button 
                  data-dropdown="packet"
                  onClick={() => {
                    const packetFilterElem = document.getElementById('packet-filter-options');
                    if (packetFilterElem) {
                      packetFilterElem.classList.toggle('hidden');
                      
                      // Close the other dropdown if open
                      const outgoingFilterElem = document.getElementById('outgoing-filter-options');
                      if (outgoingFilterElem && !outgoingFilterElem.classList.contains('hidden')) {
                        outgoingFilterElem.classList.add('hidden');
                      }
                    }
                  }}
                  className="ml-4 text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded flex items-center"
                >
                  Filter Options
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              )}
            </div>
            
            {/* Collapsible packet filter options */}
            {visibleLogTypes.has("packet") && (
              <div id="packet-filter-options" className="hidden ml-6 mt-2 p-2 bg-gray-50 rounded border border-gray-200 z-10 absolute shadow-md">
                {packetTypes.length > 0 && (
                  <div className="mt-2">
                    <div className="text-sm font-medium mb-1">Filter by Packet Type:</div>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1 thin-scrollbar">
                      {packetTypes.map(type => (
                        <div key={type} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`packet-type-${type}`}
                            checked={selectedPacketTypes.has(type)}
                            onChange={() => togglePacketType(type)}
                            className="mr-1"
                          />
                          <label htmlFor={`packet-type-${type}`} className="text-sm cursor-pointer truncate">
                            {type}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="mt-3 border-t border-gray-200 pt-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="unknown-packets"
                      checked={showUnknownPackets}
                      onChange={() => setShowUnknownPackets(!showUnknownPackets)}
                      className="mr-1"
                    />
                    <label htmlFor="unknown-packets" className="text-sm cursor-pointer">
                      Unknown Packets
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex-grow flex flex-col border border-gray-200 rounded overflow-hidden">
        <div 
          ref={logContentRef}
          className="log-content flex-grow overflow-auto thin-scrollbar"
          style={{ minHeight: "200px", maxHeight: "calc(100vh - 300px)" }}
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
                  <div className="flex items-center flex-wrap">
                    <span className="log-type text-xs font-medium mr-2 px-1 py-0.5 rounded" style={{ 
                      backgroundColor: getLogTypeColor(log.type),
                      color: "white"
                    }}>
                      {log.type.toUpperCase()}
                    </span>
                    {log.packetType && (
                      <span className="log-packet-type text-xs mr-2 px-1 py-0.5 bg-gray-200 rounded">
                        {log.packetType}
                      </span>
                    )}
                    <span className="log-timestamp text-gray-600">[{log.timestamp}]</span>
                    {log.size && (
                      <span className="log-size text-xs ml-2 text-gray-500">
                        ({log.size} bytes)
                      </span>
                    )}
                    {log.isUnknown && (
                      <span className="log-unknown text-xs ml-2 text-red-500 font-bold">
                        UNKNOWN
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
        
        <div className="text-xs text-gray-500 p-2 bg-gray-50 border-t border-gray-200 flex-shrink-0 flex justify-between items-center">
          <div className="button-controls flex gap-2">
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
          
          <div>
            Showing {filteredLogs.length} of {logs.length} logs (max: {MAX_LOG_ENTRIES})
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedLog; 