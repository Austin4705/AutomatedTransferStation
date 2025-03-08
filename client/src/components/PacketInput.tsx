import { useState, useEffect, useRef } from "react";
import { useSendJSON } from "../hooks/useSendJSON";

// Empty template and placeholder with identical structure
const EMPTY_TEMPLATE = `{
  "type": 
  
}`;

// Placeholder template with example content
const PLACEHOLDER_TEMPLATE = `{
  "type": "COMMAND_NAME",
  "parameter": "value"
}`;

const PacketInput = () => {
  const [packetJson, setPacketJson] = useState(EMPTY_TEMPLATE);
  const [error, setError] = useState<string | null>(null);
  const [keepText, setKeepText] = useState(false);
  const [rows, setRows] = useState(0);
  const [showPlaceholder, setShowPlaceholder] = useState(true);
  const sendJson = useSendJSON();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check if we should show the placeholder
  useEffect(() => {
    setShowPlaceholder(packetJson === EMPTY_TEMPLATE);
  }, [packetJson]);

  // Calculate rows based on content
  useEffect(() => {
    const lineCount = (packetJson.match(/\n/g) || []).length + 1;
    setRows(Math.max(lineCount, 4)); // Minimum 4 rows
  }, [packetJson]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!packetJson.trim()) return;
    
    try {
      // Parse the JSON to validate it
      const packetObject = JSON.parse(packetJson.trim());
      
      // Send the packet to the server
      sendJson(packetObject);
      
      // Clear the input field and any errors if keepText is false
      if (!keepText) {
        setPacketJson(EMPTY_TEMPLATE);
      }
      setError(null);
    } catch (err) {
      setError("Invalid JSON format");
    }
  };

  // Reset fields to default state
  const handleReset = () => {
    setPacketJson(EMPTY_TEMPLATE);
    setError(null);
  };

  // Handle focusing the textarea to position cursor properly
  const handleFocus = () => {
    if (textareaRef.current) {
      // If the content is just the default template, position cursor after "type":
      if (packetJson === EMPTY_TEMPLATE) {
        const textarea = textareaRef.current;
        // Position cursor after "type":
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = 10;
        }, 0);
      }
    }
  };

  // Handle tab key in textarea
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      
      // Insert tab at cursor position (2 spaces)
      const newValue = packetJson.substring(0, start) + '  ' + packetJson.substring(end);
      setPacketJson(newValue);
      
      // Move cursor after the inserted tab
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2;
          textareaRef.current.focus();
        }
      }, 0);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="packet-input-form">
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center mb-1">
          <h2 className="text-base font-medium">Custom Packet</h2>
          <div className="flex items-center gap-2">
            <div className="keep-text-checkbox">
              <input
                type="checkbox"
                id="packet-keep-text"
                checked={keepText}
                onChange={(e) => setKeepText(e.target.checked)}
              />
              <label htmlFor="packet-keep-text">
                Keep text
              </label>
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="reset-button"
            >
              Reset
            </button>
          </div>
        </div>
        <div className="parameters-container relative">
          <textarea
            ref={textareaRef}
            id="packet-json"
            value={packetJson}
            onChange={(e) => {
              setPacketJson(e.target.value);
              setError(null); // Clear error when input changes
            }}
            onKeyDown={handleKeyDown}
            className="ts-parameters-input-field w-full"
            spellCheck="false"
            wrap="off"
            rows={rows}
            onFocus={handleFocus}
          />
          {showPlaceholder && (
            <div className="placeholder-text">
              {PLACEHOLDER_TEMPLATE}
            </div>
          )}
        </div>
        
        {error && (
          <div className="error-message text-sm" style={{ color: "#e74c3c" }}>
            {error}
          </div>
        )}
        
        <div className="flex justify-end">
          <button 
            type="submit" 
            className="ts-command-send-button"
            disabled={!packetJson.trim()}
          >
            Send Packet
          </button>
        </div>
      </div>
    </form>
  );
};

export default PacketInput; 