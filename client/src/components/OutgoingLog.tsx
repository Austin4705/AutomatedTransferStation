import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";

interface OutgoingLogEntry {
  timestamp: string;
  message: string;
}

const OutgoingLog = () => {
  const [outgoingLogs, setOutgoingLogs] = useState<OutgoingLogEntry[]>([]);
  const jsonState = useRecoilValue(jsonStateAtom);
  const logContentRef = useRef<HTMLDivElement>(null);

  // Track outgoing messages
  useEffect(() => {
    // We need to create a custom event listener to capture outgoing messages
    // since the jsonState doesn't track them directly
    const handleOutgoingMessage = (event: CustomEvent) => {
      const message = event.detail;
      const newEntry: OutgoingLogEntry = {
        timestamp: new Date().toLocaleString(),
        message: typeof message === 'string' ? message : JSON.stringify(message)
      };
      
      setOutgoingLogs(prev => [...prev, newEntry]);
      
      // Scroll to bottom after update
      setTimeout(() => {
        if (logContentRef.current) {
          logContentRef.current.scrollTop = logContentRef.current.scrollHeight;
        }
      }, 100);
    };

    // Add event listener for outgoing messages
    window.addEventListener('outgoingMessage' as any, handleOutgoingMessage);
    
    // Clean up
    return () => {
      window.removeEventListener('outgoingMessage' as any, handleOutgoingMessage);
    };
  }, []);

  return (
    <div className="outgoing-log h-full flex flex-col">
      <div 
        ref={logContentRef}
        className="log-content flex-grow overflow-auto"
      >
        {outgoingLogs.length === 0 ? (
          <div className="text-gray-600 text-sm p-2">No outgoing messages logged</div>
        ) : (
          <ul className="log-list m-0 p-0" style={{ listStyle: "none" }}>
            {outgoingLogs.map((log, index) => (
              <li key={index} className="log-item p-2 text-sm border-b border-gray-100">
                <span className="log-timestamp text-gray-600">[{log.timestamp}]</span>{" "}
                <span className="log-message">{log.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="log-actions mt-2">
        <button 
          onClick={() => setOutgoingLogs([])}
          className="clear-button text-sm"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default OutgoingLog; 