import { useState, useEffect, useRef } from "react";
import { useSendJSON } from "../hooks/useSendJSON";

// Empty template with exact spacing to match placeholder
const EMPTY_TEMPLATE = `{

}`;

const TransferStationCommandInput = () => {
  const [command, setCommand] = useState("");
  const [parameters, setParameters] = useState(EMPTY_TEMPLATE);
  const [keepText, setKeepText] = useState(false);
  const [rows, setRows] = useState(0);
  const sendJson = useSendJSON();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Calculate rows based on content
  useEffect(() => {
    const lineCount = (parameters.match(/\n/g) || []).length + 1;
    setRows(Math.max(lineCount, 4)); // Minimum 4 rows
  }, [parameters]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!command.trim()) return;
    
    // Send TS_COMMAND to the server
    sendJson({
      type: "TS_COMMAND",
      command: command.trim(),
      parameters: parameters.trim()
    });
    
    // Clear the input fields if keepText is false
    if (!keepText) {
      setCommand("");
      setParameters(EMPTY_TEMPLATE);
    }
  };

  // Handle focusing the textarea to position cursor properly
  const handleFocus = () => {
    if (textareaRef.current) {
      // If the content is just the default template, position cursor between braces
      if (parameters === EMPTY_TEMPLATE) {
        const textarea = textareaRef.current;
        // Position cursor after the first newline
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = 2;
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
      const newValue = parameters.substring(0, start) + '  ' + parameters.substring(end);
      setParameters(newValue);
      
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
    <form onSubmit={handleSubmit} className="ts-command-input-form">
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center mb-1">
          <h2 className="text-base font-medium">Transfer Station Command</h2>
          <div className="keep-text-checkbox">
            <input
              type="checkbox"
              id="ts-keep-text"
              checked={keepText}
              onChange={(e) => setKeepText(e.target.checked)}
            />
            <label htmlFor="ts-keep-text">
              Keep text
            </label>
          </div>
        </div>
        <div className="input-group flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter transfer station command..."
            className="ts-command-input-field flex-grow"
          />
          <button 
            type="submit" 
            className="ts-command-send-button"
            disabled={!command.trim()}
          >
            Send
          </button>
        </div>
        <div className="parameters-container relative">
          <label htmlFor="ts-parameters" className="block text-sm font-medium text-gray-700 mb-1">
            Parameters
          </label>
          <textarea
            ref={textareaRef}
            id="ts-parameters"
            value={parameters}
            onChange={(e) => setParameters(e.target.value)}
            onKeyDown={handleKeyDown}
            className="ts-parameters-input-field w-full"
            spellCheck="false"
            rows={rows}
            onFocus={handleFocus}
          />
        </div>
        <div className="text-xs text-gray-500">
          Example: "move_to" with parameters {"{"}"x": 10, "y": 20, "z": 30{"}"}
        </div>
      </div>
    </form>
  );
};

export default TransferStationCommandInput; 