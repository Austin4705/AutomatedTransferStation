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


const UnifiedLog = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [visibleLogTypes, setVisibleLogTypes] = useState<Set<LogType>>(new Set(["command", "response", "outgoing", "packet"]));
  const [showUnknownPackets, setShowUnknownPackets] = useState<boolean>(true);
  const [showUnknownOutgoing, setShowUnknownOutgoing] = useState<boolean>(true);
  const [selectedPacketTypes, setSelectedPacketTypes] = useState<Set<string>>(new Set());
  const [selectedOutgoingTypes, setSelectedOutgoingTypes] = useState<Set<string>>(new Set());
  const [definedPacketTypes, setDefinedPacketTypes] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState<boolean>(() => {
    // Try to get the setting from localStorage, default to true
    const savedSetting = localStorage.getItem('log-auto-scroll');
    return savedSetting !== null ? savedSetting === 'true' : true;
  });
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const logContentRef = useRef<HTMLDivElement>(null);
  const packetDefsLoaded = useRef<boolean>(false);
  // Add a ref to track the last processed message to avoid duplicates after clearing
  const lastProcessedMessageRef = useRef<any>(undefined);
  // Add a ref to track if logs were manually cleared
  const logsManuallyCleared = useRef<boolean>(false);
  // Add a cooldown period after clearing logs
  const clearCooldownRef = useRef<boolean>(false);
  // Add a message deduplication cache
  const recentMessagesRef = useRef<Set<string>>(new Set());
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  // Add state to track if certain log types should be hidden completely
  const [hiddenLogTypes, setHiddenLogTypes] = useState<Set<LogType>>(new Set());

  // Update localStorage when auto-scroll setting changes
  useEffect(() => {
    localStorage.setItem('log-auto-scroll', autoScroll.toString());
  }, [autoScroll]);

  // Listen for logs-visibility-changed event
  useEffect(() => {
    const handleLogsVisibilityEvent = (event: CustomEvent) => {
      const newHiddenLogTypes = new Set(hiddenLogTypes);
      
      if (event.detail) {
        // If commandLogs is false, hide command logs
        if (event.detail.commandLogs === false) {
          newHiddenLogTypes.add("command");
        } else if (event.detail.commandLogs === true) {
          newHiddenLogTypes.delete("command");
        }
        
        // If responseLogs is false, hide response logs
        if (event.detail.responseLogs === false) {
          newHiddenLogTypes.add("response");
        } else if (event.detail.responseLogs === true) {
          newHiddenLogTypes.delete("response");
        }
        
        setHiddenLogTypes(newHiddenLogTypes);
        
        // Update visible log types
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
    
    // Add event listener
    document.addEventListener('logs-visibility-changed', handleLogsVisibilityEvent as EventListener);
    
    // Clean up
    return () => {
      document.removeEventListener('logs-visibility-changed', handleLogsVisibilityEvent as EventListener);
    };
  }, [hiddenLogTypes, visibleLogTypes]);

  // Load packet definitions from document
  useEffect(() => {
    const loadPacketDefinitions = async () => {
      if (packetDefsLoaded.current) return;
      
      try {
        // Initialize packet manager if needed
        if (!PacketManager.isInitialized()) {
          console.log("Initializing packet manager from UnifiedLog...");
          await PacketManager.initialize();
        }
        
        // Load packet definitions from the shared directory
        const response = await fetch('/shared/packet_definitions.json');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const packetDefs = await response.json();
        
        // Extract packet types from definitions
        const packetTypes = Object.keys(packetDefs.packets || {});
        
        // Create the allPacketTypes array for use throughout the component
        const allPacketTypes = packetTypes;
        
        // Combine with common packet types
        setDefinedPacketTypes(allPacketTypes);
        
        // Initialize all packet types as selected
        setSelectedPacketTypes(new Set(allPacketTypes));
        
        // Use the same packet types for outgoing messages
        setSelectedOutgoingTypes(new Set(allPacketTypes));
        
        packetDefsLoaded.current = true;
        
        console.log("Loaded packet types from definitions:", allPacketTypes);
      } catch (error) {
        console.error('Failed to load packet definitions:', error);
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

  // Extract unique outgoing message types from logs and combine with defined types
  const outgoingTypes = useMemo(() => {
    const typesFromLogs = new Set<string>();
    logs.forEach(log => {
      if (log.type === "outgoing" && log.packetType) {
        typesFromLogs.add(log.packetType);
      }
    });
    
    // Combine with defined packet types (using the same source as packets)
    const allTypes = new Set([...definedPacketTypes, ...typesFromLogs]);
    return Array.from(allTypes).sort();
  }, [logs, definedPacketTypes]);

  // Helper function to add logs while respecting the maximum limit
  const addLogs = (newLogs: LogEntry[], replace = false) => {
    // Skip if we're in a cooldown period after clearing
    if (clearCooldownRef.current) {
      console.log("Skipping log addition during cooldown period");
      return;
    }
    
    // Deduplicate logs before adding them
    const uniqueLogs = newLogs.filter(newLog => {
      // Create a unique key for this log
      const logKey = `${newLog.type}-${newLog.packetType}-${newLog.message}`;
      
      // Check if we've seen this message recently
      if (recentMessagesRef.current.has(logKey)) {
        console.log("Preventing duplicate log:", logKey);
        return false;
      }
      
      // Add to recent messages cache
      recentMessagesRef.current.add(logKey);
      
      // Limit the size of the cache to prevent memory leaks
      if (recentMessagesRef.current.size > 1000) {
        const oldestKey = Array.from(recentMessagesRef.current)[0];
        recentMessagesRef.current.delete(oldestKey);
      }
      
      return true;
    });
    
    // Only proceed if there are unique logs to add
    if (uniqueLogs.length === 0) {
      return;
    }
    
    if (logContentRef.current && !autoScroll) {
      // Save current scroll position before updating
      const scrollContainer = logContentRef.current;
      const scrollPosition = scrollContainer.scrollTop;
      const isScrolledToBottom = scrollContainer.scrollHeight - scrollContainer.clientHeight <= scrollContainer.scrollTop + 5;
      
      setLogs(prevLogs => {
        // If replacing logs of a specific type, filter out that type first
        const filteredLogs = replace 
          ? prevLogs.filter(log => log.type !== uniqueLogs[0]?.type) // Filter by type directly
          : prevLogs;
        
        // Log what's happening for debugging
        if (replace) {
          console.log(`Replacing ${prevLogs.filter(log => log.type === uniqueLogs[0]?.type).length} ${uniqueLogs[0]?.type} logs with ${uniqueLogs.length} new logs`);
        }
        
        // Combine existing and new logs
        const combinedLogs = [...filteredLogs, ...uniqueLogs];
        
        // Trim to maximum size if needed
        return combinedLogs.length > MAX_LOG_ENTRIES 
          ? combinedLogs.slice(combinedLogs.length - MAX_LOG_ENTRIES) 
          : combinedLogs;
      });
      
      // Restore scroll position after the next render
      setTimeout(() => {
        if (scrollContainer) {
          if (isScrolledToBottom) {
            // If user was at the bottom, keep them at the bottom
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
          } else {
            // Otherwise, restore the previous scroll position
            scrollContainer.scrollTop = scrollPosition;
          }
        }
      }, 0);
    } else {
      // Standard behavior without scroll position preservation
      setLogs(prevLogs => {
        // If replacing logs of a specific type, filter out that type first
        const filteredLogs = replace 
          ? prevLogs.filter(log => log.type !== uniqueLogs[0]?.type) // Filter by type directly
          : prevLogs;
        
        // Log what's happening for debugging
        if (replace) {
          console.log(`Replacing ${prevLogs.filter(log => log.type === uniqueLogs[0]?.type).length} ${uniqueLogs[0]?.type} logs with ${uniqueLogs.length} new logs`);
        }
        
        // Combine existing and new logs
        const combinedLogs = [...filteredLogs, ...uniqueLogs];
        
        // Trim to maximum size if needed
        return combinedLogs.length > MAX_LOG_ENTRIES 
          ? combinedLogs.slice(combinedLogs.length - MAX_LOG_ENTRIES) 
          : combinedLogs;
      });
    }
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
      
      // Determine the log type based on packet type
      let logType: "command" | "response" | "packet" = "packet";
      
      // Check if this is a command packet
      if (packetInfo.type === "COMMAND" || 
          (packetInfo.data && (packetInfo.data.command || 
          (Array.isArray(packetInfo.data.commands) && packetInfo.data.commands.length > 0)))) {
        logType = "command";
      }
      // Check if this is a response packet
      else if (packetInfo.type === "RESPONSE" || 
               packetInfo.type === "COMMAND_RESULT" || 
               packetInfo.type === "ERROR" ||
               packetInfo.type === "RESPONSE_LOG_RESPONSE" ||
               (packetInfo.data && (packetInfo.data.response || packetInfo.data.message ||
               (Array.isArray(packetInfo.data.responses) && packetInfo.data.responses.length > 0)))) {
        logType = "response";
      }
      
      // Create a message content based on the log type
      let messageContent: string;
      if (logType === "command") {
        // For commands, show the command content if available
        messageContent = packetInfo.data && packetInfo.data.command 
          ? packetInfo.data.command
          : rawPacket;
      } else if (logType === "response") {
        // For responses, show the response content if available
        messageContent = packetInfo.data && (packetInfo.data.response || packetInfo.data.message)
          ? (packetInfo.data.response || packetInfo.data.message)
          : rawPacket;
      } else {
        // For regular packets, show the raw packet
        messageContent = rawPacket;
      }
      
      const newEntry: LogEntry = {
        timestamp: new Date(packetInfo.timestamp).toLocaleString(),
        message: messageContent,
        type: logType, // Use the determined log type
        rawData: packetInfo.data,
        size: packetInfo.size,
        packetType: packetInfo.type,
        isUnknown
      };
      
      // Create a unique key for this packet to check for duplication
      const packetKey = `${logType}-${packetInfo.type}-${packetInfo.timestamp}`;
      
      // Check if this entry would be a duplicate
      const isDuplicate = logs.some(log => 
        log.type === logType && 
        log.packetType === packetInfo.type && 
        log.timestamp === newEntry.timestamp
      );
      
      if (!isDuplicate) {
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
      }
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
          isUnknown = !definedPacketTypes.includes(messageType);
        } else if (typeof message === 'string') {
          try {
            const parsed = JSON.parse(message);
            if (parsed && parsed.type) {
              messageType = parsed.type;
              // Check if this is an unknown packet type
              isUnknown =  
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
    // Only scroll if auto-scroll is enabled
    if (autoScroll) {
      // console.log("Auto-scroll is enabled, scrolling to bottom");
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    } else {
      // console.log("Auto-scroll is disabled, not scrolling to bottom");
    }
  };

  // Function to request command logs
  const requestCommandLogs = () => {
    sendJson({
      type: "REQUEST_LOG_COMMANDS",
    });
    
    // Flag to scroll once when the response comes in
    window.sessionStorage.setItem('log_scroll_on_next_command_response', 'true');
  };

  // Function to request response logs
  const requestResponseLogs = () => {
    sendJson({
      type: "REQUEST_LOG_RESPONSE",
    });
    
    // Flag to scroll once when the response comes in
    window.sessionStorage.setItem('log_scroll_on_next_response_response', 'true');
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

  // Filter logs based on visibility settings and hidden log types
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      // Filter by log type visibility
      if (!visibleLogTypes.has(log.type) || hiddenLogTypes.has(log.type)) {
        return false;
      }
      
      // Filter by packet type if it's a packet
      if (log.type === "packet" && log.packetType) {
        // Filter unknown packets based on setting
        if (!showUnknownPackets && log.isUnknown) {
          return false;
        }
        
        // Filter by selected packet types
        if (selectedPacketTypes.size > 0 && !selectedPacketTypes.has(log.packetType)) {
          return false;
        }
      }
      
      // Filter by outgoing message type
      if (log.type === "outgoing" && log.packetType) {
        // Filter unknown outgoing messages based on setting
        if (!showUnknownOutgoing && log.isUnknown) {
          return false;
        }
        
        // Filter by selected outgoing types
        if (selectedOutgoingTypes.size > 0 && !selectedOutgoingTypes.has(log.packetType)) {
          return false;
        }
      }
      
      return true;
    });
  }, [logs, visibleLogTypes, hiddenLogTypes, showUnknownPackets, showUnknownOutgoing, selectedPacketTypes, selectedOutgoingTypes]);

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
    console.log("Clearing logs and setting cooldown period");
    
    // Set the cooldown flag to prevent immediate additions
    clearCooldownRef.current = true;
    
    setLogs([]); // Directly set logs to an empty array
    
    // Mark that logs were manually cleared to prevent immediate re-adding
    logsManuallyCleared.current = true;
    
    // Reset the last processed message reference
    lastProcessedMessageRef.current = undefined;
    
    // Clear the message deduplication cache
    recentMessagesRef.current.clear();
    
    // Reset any tracking variables that might cause issues
    // This helps prevent the last message from reappearing
    const event = new CustomEvent('logs-cleared', {
      detail: { timestamp: new Date().getTime() }
    });
    document.dispatchEvent(event);
    
    // Force stop all pending log requests by adding a small delay
    // before new log messages can be processed
    setTimeout(() => {
      // After a brief delay, we can allow processing messages again
      clearCooldownRef.current = false;
      console.log("Log clearing complete - ready for new messages");
    }, 1000); // Use a longer cooldown period of 1 second
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

  // Process incoming messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    // Skip if we're in a cooldown period after clearing
    if (clearCooldownRef.current) {
      console.log("Skipping message processing during cooldown period");
      return;
    }

    // Skip if this is the same message we already processed
    if (lastProcessedMessageRef.current === jsonState.lastJsonMessage) {
      return;
    }

    // Create a message key for deduplication
    const message = jsonState.lastJsonMessage as BaseMessage;
    const messageKey = `${message.type}-${JSON.stringify(message)}`;
    
    // Skip if we've seen this exact message recently
    if (recentMessagesRef.current.has(messageKey)) {
      console.log("Skipping duplicate message:", messageKey);
      return;
    }
    
    // Add to recent messages cache
    recentMessagesRef.current.add(messageKey);

    // Update the last processed message
    lastProcessedMessageRef.current = jsonState.lastJsonMessage;
    
    // If logs were manually cleared, we need to reset the flag
    // but only process new messages after clearing
    if (logsManuallyCleared.current) {
      // Simply reset the flag and skip all message processing until new messages arrive
      logsManuallyCleared.current = false;
      
      // Skip all message processing right after clearing logs
      // This prevents duplicating commands and responses right after clear
      return;
    }
    
    // Handle command messages
    if (message.type === "COMMAND") {
      const commandMessage = message as CommandMessage;
      
      // Check if this command is already in the logs to prevent duplicates
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
        scrollToBottom();
      }
    }
    // Handle bulk command logs
    else if (message.type === "RESPONSE_LOG_COMMANDS" && Array.isArray((message as CommandMessage).commands)) {
      const commandMessage = message as CommandMessage;
      // Only process if there are actual commands in the response
      if (commandMessage.commands!.length > 0) {
        const commandLogs: LogEntry[] = commandMessage.commands!.map((cmd: any) => ({
          timestamp: new Date(cmd.timestamp || Date.now()).toLocaleString(),
          message: cmd.command || JSON.stringify(cmd),
          type: "command",
          rawData: cmd,
          packetType: "COMMAND"
        }));
        
        // Always replace all command logs with the new ones
        addLogs(commandLogs, true);
        
        // Check if we should scroll for this response
        const shouldScrollForThisResponse = window.sessionStorage.getItem('log_scroll_on_next_command_response') === 'true';
        if (shouldScrollForThisResponse) {
          console.log("Performing one-time scroll for command response");
          window.sessionStorage.removeItem('log_scroll_on_next_command_response');
          
          // Manually scroll without using auto-scroll
          setTimeout(() => {
            if (logContentRef.current) {
              logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
            }
          }, 100);
        } else {
          // Normal scrolling based on auto-scroll setting
          scrollToBottom(); // This will only scroll if auto-scroll is enabled
        }
        
        console.log(`Received ${commandLogs.length} command logs`);
      } else {
        console.log("Received empty command logs response");
      }
    }
    
    // Handle response messages
    else if (message.type === "RESPONSE" || message.type === "COMMAND_RESULT" || message.type === "ERROR") {
      const responseMessage = message as ResponseMessage;
      
      // Check if this response is already in the logs to prevent duplicates
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
        scrollToBottom(); // This will only scroll if auto-scroll is enabled
      }
    }
    

    // ... existing code for other message types ...
  }, [jsonState.lastJsonMessage, addLogs, scrollToBottom, logs]);

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

export default UnifiedLog; 