import { useState } from "react";
import { useSendJSON } from "../hooks/useSendJSON";

const CommandInput = () => {
  const [command, setCommand] = useState("");
  const sendJson = useSendJSON();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!command.trim()) return;
    
    // Send command to the server
    sendJson({
      type: "SEND_COMMAND",
      command: command.trim()
    });
    
    // Clear the input field
    setCommand("");
  };

  return (
    <form onSubmit={handleSubmit} className="command-input-form">
      <div className="input-group flex gap-2">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Enter command..."
          className="command-input-field flex-grow"
        />
        <button 
          type="submit" 
          className="command-send-button"
          disabled={!command.trim()}
        >
          Send
        </button>
      </div>
    </form>
  );
};

export default CommandInput; 