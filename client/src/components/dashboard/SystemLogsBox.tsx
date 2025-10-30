import { useState, useEffect, useRef, useMemo } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { useSendJSON } from "../../hooks/useSendJSON";
import { PacketManager } from "../../packets/PacketHandler";

const MAX_LOG_ENTRIES = 1000;

interface LogEntry {
  timestamp: string;
  message: string;
  type: "command" | "response" | "outgoing" | "packet";
  rawData?: any;
  size?: number;
  packetType?: string;
  isUnknown?: boolean;
}

type LogType = "command" | "response" | "outgoing" | "packet";

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


const SystemLogsBox = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [visibleLogTypes, setVisibleLogTypes] = useState<Set<LogType>>(new Set(["command", "response", "outgoing", "packet"]));
  const [showUnknownPackets, setShowUnknownPackets] = useState<boolean>(true);
  const [showUnknownOutgoing, setShowUnknownOutgoing] = useState<boolean>(true);
  const [selectedPacketTypes, setSelectedPacketTypes] = useState<Set<string>>(new Set());
  const [selectedOutgoingTypes, setSelectedOutgoingTypes] = useState<Set<string>>(new Set());
  const [definedPacketTypes, setDefinedPacketTypes] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState<boolean>(() => {
    const savedSetting = localStorage.getItem('log-auto-scroll');
    return savedSetting !== null ? savedSetting === 'true' : true;
  });
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);
  const packetDefsLoaded = useRef<boolean>(false);
  const lastProcessedMessageRef = useRef<any>(undefined);
  const logsManuallyCleared = useRef<boolean>(false);
  const clearCooldownRef = useRef<boolean>(false);
  const recentMessagesRef = useRef<Set<string>>(new Set());
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [hiddenLogTypes, setHiddenLogTypes] = useState<Set<LogType>>(new Set());

  useEffect(() => {
    localStorage.setItem('log-auto-scroll', autoScroll.toString());
  }, [autoScroll]);

  useEffect(() => {
    const handleLogsVisibilityEvent = (event: CustomEvent) => {
      const newHiddenLogTypes = new Set(hiddenLogTypes);
      
      if (event.detail) {
        if (event.detail.commandLogs === false) {
          newHiddenLogTypes.add("command");
        } else if (event.detail.commandLogs === true) {
          newHiddenLogTypes.delete("command");
        }
        
        if (event.detail.responseLogs === false) {
          newHiddenLogTypes.add("response");
        } else if (event.detail.responseLogs === true) {
          newHiddenLogTypes.delete("response");
        }
        
        setHiddenLogTypes(newHiddenLogTypes);
        
        const newVisibleLogTypes = new Set(visibleLogTypes);
        if (event.detail.commandLogs === false) {
          newVisibleLogTypes.delete("command");
        } else if (event.detail.commandLogs === true) {
          newVisibleLogTypes.add("command");
        }
        
        if (event.detail.responseLogs === false) {
          newVisibleLogTypes.delete("response");
        } else if (event.detail.responseLogs === true) {
          newVisibleLogTypes.add("response");
        }
        
        setVisibleLogTypes(newVisibleLogTypes);
      }
    };
    
    document.addEventListener('logs-visibility-changed', handleLogsVisibilityEvent as EventListener);
    
    return () => {
      document.removeEventListener('logs-visibility-changed', handleLogsVisibilityEvent as EventListener);
    };
  }, [hiddenLogTypes, visibleLogTypes]);

  useEffect(() => {
    const loadPacketDefinitions = async () => {
      if (packetDefsLoaded.current) return;
      
      try {
        if (!PacketManager.isInitialized()) {
          console.log("Initializing packet manager from UnifiedLog...");
          await PacketManager.initialize();
        }
        
        const response = await fetch('/shared/packet_definitions.json');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const packetDefs = await response.json();
        
        const packetTypes = Object.keys(packetDefs.packets || {});
        
        const allPacketTypes = packetTypes;
        
        setDefinedPacketTypes(allPacketTypes);
        
        setSelectedPacketTypes(new Set(allPacketTypes));
        
        setSelectedOutgoingTypes(new Set(allPacketTypes));
        
        packetDefsLoaded.current = true;
        
        console.log("Loaded packet types from definitions:", allPacketTypes);
      } catch (error) {
        console.error('Failed to load packet definitions:', error);
      }
    };
    
    loadPacketDefinitions();
  }, []);

  const packetTypes = useMemo(() => {
    const typesFromLogs = new Set<string>();
    logs.forEach(log => {
      if (log.type === "packet" && log.packetType) {
        typesFromLogs.add(log.packetType);
      }
    });
    
    const allTypes = new Set([...definedPacketTypes, ...typesFromLogs]);
    return Array.from(allTypes).sort();
  }, [logs, definedPacketTypes]);

  const outgoingTypes = useMemo(() => {
    const typesFromLogs = new Set<string>();
    logs.forEach(log => {
      if (log.type === "outgoing" && log.packetType) {
        typesFromLogs.add(log.packetType);
      }
    });
    
    const allTypes = new Set([...definedPacketTypes, ...typesFromLogs]);
    return Array.from(allTypes).sort();
  }, [logs, definedPacketTypes]);

  const addLogs = (newLogs: LogEntry[], replace = false) => {
    if (clearCooldownRef.current) {
      return;
    }
    
    const uniqueLogs = newLogs.filter(newLog => {
      const logKey = `${newLog.type}-${newLog.packetType}-${newLog.message}`;
      
      if (recentMessagesRef.current.has(logKey)) {
        return false;
      }
      
      recentMessagesRef.current.add(logKey);
      
      if (recentMessagesRef.current.size > 1000) {
        const oldestKey = Array.from(recentMessagesRef.current)[0];
        recentMessagesRef.current.delete(oldestKey);
      }
      
      return true;
    });
    
    if (uniqueLogs.length === 0) {
      return;
    }
    
    setLogs(prevLogs => {
      const filteredLogs = replace 
        ? prevLogs.filter(log => log.type !== uniqueLogs[0]?.type)
        : prevLogs;
      
      if (replace) {
        console.log(`Replacing ${prevLogs.filter(log => log.type === uniqueLogs[0]?.type).length} ${uniqueLogs[0]?.type} logs with ${uniqueLogs.length} new logs`);
      }
      
      const combinedLogs = [...filteredLogs, ...uniqueLogs];
      
      return combinedLogs.length > MAX_LOG_ENTRIES 
        ? combinedLogs.slice(combinedLogs.length - MAX_LOG_ENTRIES) 
        : combinedLogs;
    });
  };

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

  useEffect(() => {
    const unsubscribe = PacketManager.registerTrafficListener((packetInfo) => {
      const rawPacket = JSON.stringify({
        type: packetInfo.type,
        data: packetInfo.data
      });
      
      const isUnknown = !PacketManager.isKnownPacketType(packetInfo.type);
      
      let logType: "command" | "response" | "packet" = "packet";
      
      if (packetInfo.type === "COMMAND" || 
          (packetInfo.data && (packetInfo.data.command || 
          (Array.isArray(packetInfo.data.commands) && packetInfo.data.commands.length > 0)))) {
        logType = "command";
      }
      else if (packetInfo.type === "RESPONSE" || 
               packetInfo.type === "COMMAND_RESULT" || 
               packetInfo.type === "ERROR" ||
               packetInfo.type === "RESPONSE_LOG_RESPONSE" ||
               (packetInfo.data && (packetInfo.data.response || packetInfo.data.message ||
               (Array.isArray(packetInfo.data.responses) && packetInfo.data.responses.length > 0)))) {
        logType = "response";
      }
      
      let messageContent: string;
      if (logType === "command") {
        messageContent = packetInfo.data && packetInfo.data.command 
          ? packetInfo.data.command
          : rawPacket;
      } else if (logType === "response") {
        messageContent = packetInfo.data && (packetInfo.data.response || packetInfo.data.message)
          ? (packetInfo.data.response || packetInfo.data.message)
          : rawPacket;
      } else {
        messageContent = rawPacket;
      }
      
      const newEntry: LogEntry = {
        timestamp: new Date(packetInfo.timestamp).toLocaleString(),
        message: messageContent,
        type: logType,
        rawData: packetInfo.data,
        size: packetInfo.size,
        packetType: packetInfo.type,
        isUnknown
      };
      
      const packetKey = `${logType}-${packetInfo.type}-${packetInfo.timestamp}`;
      
      const isDuplicate = logs.some(log => 
        log.type === logType && 
        log.packetType === packetInfo.type && 
        log.timestamp === newEntry.timestamp
      );
      
      if (!isDuplicate) {
        setLogs(prevLogs => {
          const newLogs = [...prevLogs, newEntry];
          return newLogs.length > MAX_LOG_ENTRIES 
            ? newLogs.slice(newLogs.length - MAX_LOG_ENTRIES) 
            : newLogs;
        });
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    const handleOutgoingMessage = (event: CustomEvent) => {
      const message = event.detail;
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      
      let messageType = "";
      let isUnknown = false;
      
      try {
        if (typeof message === 'object' && message.type) {
          messageType = message.type;
          isUnknown = !definedPacketTypes.includes(messageType);
        } else if (typeof message === 'string') {
          try {
            const parsed = JSON.parse(message);
            if (parsed && parsed.type) {
              messageType = parsed.type;
              isUnknown =  
        !definedPacketTypes.includes(messageType);
            }
          } catch {
            isUnknown = true;
          }
        }
      } catch (e) {
        isUnknown = true;
      }
      
      const newEntry: LogEntry = {
        timestamp: new Date().toLocaleString(),
        message: messageStr,
        type: "outgoing",
        packetType: messageType,
        isUnknown
      };
      
      setLogs(prevLogs => {
        const newLogs = [...prevLogs, newEntry];
        return newLogs.length > MAX_LOG_ENTRIES 
          ? newLogs.slice(newLogs.length - MAX_LOG_ENTRIES) 
          : newLogs;
      });
      
      if (autoScroll) {
        scrollToBottom();
      }
    };

    window.addEventListener('outgoingMessage' as any, handleOutgoingMessage);
    
    return () => {
      window.removeEventListener('outgoingMessage' as any, handleOutgoingMessage);
    };
  }, [definedPacketTypes, autoScroll]);

  const scrollToBottom = () => {
    setTimeout(() => {
      if (logContentRef.current) {
        logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
      }
    }, 100);
  };

  const requestCommandLogs = () => {
    sendJson({
      type: "REQUEST_LOG_COMMANDS",
    });
    
    window.sessionStorage.setItem('log_scroll_on_next_command_response', 'true');
  };

  const requestResponseLogs = () => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
    
    window.sessionStorage.setItem('log_scroll_on_next_response_response', 'true');
  };

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

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (!visibleLogTypes.has(log.type) || hiddenLogTypes.has(log.type)) {
        return false;
      }
      
      if (log.type === "packet" && log.packetType) {
        if (!showUnknownPackets && log.isUnknown) {
          return false;
        }
        
        if (selectedPacketTypes.size > 0 && !selectedPacketTypes.has(log.packetType)) {
          return false;
        }
      }
      
      if (log.type === "outgoing" && log.packetType) {
        if (!showUnknownOutgoing && log.isUnknown) {
          return false;
        }
        
        if (selectedOutgoingTypes.size > 0 && !selectedOutgoingTypes.has(log.packetType)) {
          return false;
        }
      }
      
      return true;
    });
  }, [logs, visibleLogTypes, hiddenLogTypes, showUnknownPackets, showUnknownOutgoing, selectedPacketTypes, selectedOutgoingTypes]);

  const getLogTypeColor = (type: "command" | "response" | "outgoing" | "packet") => {
    switch (type) {
      case "command":
        return "#3498db";
      case "response":
        return "#2ecc71";
      case "outgoing":
        return "#e67e22";
      case "packet":
        return "#9b59b6";
      default:
        return "#718096";
    }
  };

  const clearLogs = () => {
    console.log("Clearing logs and setting cooldown period");
    
    clearCooldownRef.current = true;
    
    setLogs([]);
    
    logsManuallyCleared.current = true;
    
    lastProcessedMessageRef.current = undefined;
    
    recentMessagesRef.current.clear();
    
    const event = new CustomEvent('logs-cleared', {
      detail: { timestamp: new Date().getTime() }
    });
    document.dispatchEvent(event);
    
    setTimeout(() => {
      clearCooldownRef.current = false;
      console.log("Log clearing complete - ready for new messages");
    }, 1000);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const outgoingFilterElem = document.getElementById('outgoing-filter-options');
      const packetFilterElem = document.getElementById('packet-filter-options');
      
      if (outgoingFilterElem && !outgoingFilterElem.classList.contains('hidden')) {
        const outgoingButton = document.querySelector('[data-dropdown="outgoing"]');
        if (
          !outgoingFilterElem.contains(event.target as Node) && 
          (!outgoingButton || !outgoingButton.contains(event.target as Node))
        ) {
          outgoingFilterElem.classList.add('hidden');
        }
      }
      
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

  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    if (clearCooldownRef.current) {
      return;
    }

    if (lastProcessedMessageRef.current === jsonState.lastJsonMessage) {
      return;
    }

    const message = jsonState.lastJsonMessage as BaseMessage;
    const messageKey = `${message.type}-${JSON.stringify(message)}`;
    
    if (recentMessagesRef.current.has(messageKey)) {
      return;
    }
    
    recentMessagesRef.current.add(messageKey);

    lastProcessedMessageRef.current = jsonState.lastJsonMessage;
    
    if (logsManuallyCleared.current) {
      logsManuallyCleared.current = false;
      
      return;
    }
    
    if (message.type === "COMMAND") {
      const commandMessage = message as CommandMessage;
      
      const isDuplicate = logs.some(log => 
        log.type === "command" && 
        log.packetType === "COMMAND" && 
        log.message === (commandMessage.command || JSON.stringify(message))
      );
      
      if (!isDuplicate) {
        const newEntry: LogEntry = {
          timestamp: new Date().toLocaleString(),
          message: commandMessage.command || JSON.stringify(message),
          type: "command",
          rawData: message,
          packetType: message.type
        };
        
        addLogs([newEntry]);
        
        if (autoScroll) {
          scrollToBottom();
        }
      }
    }
    else if (message.type === "RESPONSE_LOG_COMMANDS" && Array.isArray((message as CommandMessage).commands)) {
      const commandMessage = message as CommandMessage;
      if (commandMessage.commands!.length > 0) {
        const commandLogs: LogEntry[] = commandMessage.commands!.map((cmd: any) => ({
          timestamp: new Date(cmd.timestamp || Date.now()).toLocaleString(),
          message: cmd.command || JSON.stringify(cmd),
          type: "command",
          rawData: cmd,
          packetType: "COMMAND"
        }));
        
        addLogs(commandLogs, true);
        
        const shouldScrollForThisResponse = window.sessionStorage.getItem('log_scroll_on_next_command_response') === 'true';
        if (shouldScrollForThisResponse) {
          console.log("Performing one-time scroll for command response");
          window.sessionStorage.removeItem('log_scroll_on_next_command_response');
          
          setTimeout(() => {
            if (logContentRef.current) {
              logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
            }
          }, 100);
        } else if (autoScroll) {
          scrollToBottom();
        }
        
        console.log(`Received ${commandLogs.length} command logs`);
      } else {
        console.log("Received empty command logs response");
      }
    }
    
    else if (message.type === "RESPONSE" || message.type === "COMMAND_RESULT" || message.type === "ERROR") {
      const responseMessage = message as ResponseMessage;
      
      const isDuplicate = logs.some(log => 
        log.type === "response" && 
        log.packetType === message.type && 
        log.message === (responseMessage.message || responseMessage.response || JSON.stringify(message))
      );
      
      if (!isDuplicate) {
        const newEntry: LogEntry = {
          timestamp: new Date().toLocaleString(),
          message: responseMessage.message || responseMessage.response || JSON.stringify(message),
          type: "response",
          rawData: message,
          packetType: message.type
        };
        
        addLogs([newEntry]);
        
        if (autoScroll) {
          scrollToBottom();
        }
      }
    }
  }, [jsonState.lastJsonMessage, addLogs, scrollToBottom, logs, autoScroll]);

  return (
    <div className="unified-log h-full flex flex-col">
      <div className="log-controls p-2 bg-gray-100 rounded mb-2 overflow-visible">
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
              
              {visibleLogTypes.has("outgoing") && (
                <button 
                  data-dropdown="outgoing"
                  onClick={() => {
                    const outgoingFilterElem = document.getElementById('outgoing-filter-options');
                    if (outgoingFilterElem) {
                      outgoingFilterElem.classList.toggle('hidden');
                      
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
              
              {visibleLogTypes.has("packet") && (
                <button 
                  data-dropdown="packet"
                  onClick={() => {
                    const packetFilterElem = document.getElementById('packet-filter-options');
                    if (packetFilterElem) {
                      packetFilterElem.classList.toggle('hidden');
                      
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
              onClick={clearLogs}
              className="clear-button text-sm bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded"
            >
              Clear
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto-scroll"
                checked={autoScroll}
                onChange={() => setAutoScroll(!autoScroll)}
                className="mr-2"
              />
              <label htmlFor="auto-scroll" className="text-sm cursor-pointer">
                Auto-scroll
              </label>
              
              {/* Manual scroll button when auto-scroll is disabled */}
              {!autoScroll && (
                <button 
                  onClick={() => {
                    if (logContentRef.current) {
                      logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
                    }
                  }}
                  className="ml-2 text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded"
                >
                  Scroll to Bottom
                </button>
              )}
            </div>
            
            <div>
              Showing {filteredLogs.length} of {logs.length} logs (max: {MAX_LOG_ENTRIES})
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemLogsBox; 