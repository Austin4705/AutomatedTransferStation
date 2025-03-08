import { useState } from "react";
import { useSendJSON } from "../hooks/useSendJSON";

const CommandInput = () => {
  const [command, setCommand] = useState("");
  const [keepText, setKeepText] = useState(false);
  const sendJson = useSendJSON();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!command.trim()) return;
    
    // Send command to the server
    sendJson({
      type: "SEND_COMMAND",
      command: command.trim()
    });
    
    // Clear the input field if keepText is false
    if (!keepText) {
      setCommand("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="command-input-form">
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center mb-1">
          <h2 className="text-base font-medium">Custom Command</h2>
          <div className="keep-text-checkbox">
            <input
              type="checkbox"
              id="command-keep-text"
              checked={keepText}
              onChange={(e) => setKeepText(e.target.checked)}
            />
            <label htmlFor="command-keep-text">
              Keep text
            </label>
          </div>
        </div>
        <div className="input-group flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter command..."
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
      </div>
    </form>
  );
};

export default CommandInput; 