import { useState } from "react";
import { useSendJSON } from "../hooks/useSendJSON";

const PacketInput = () => {
  const [packetJson, setPacketJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const sendJson = useSendJSON();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!packetJson.trim()) return;
    
    try {
      // Parse the JSON to validate it
      const packetObject = JSON.parse(packetJson.trim());
      
      // Send the packet to the server
      sendJson(packetObject);
      
      // Clear the input field and any errors
      setPacketJson("");
      setError(null);
    } catch (err) {
      setError("Invalid JSON format");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="packet-input-form">
      <div className="input-group flex flex-col gap-2">
        <textarea
          value={packetJson}
          onChange={(e) => {
            setPacketJson(e.target.value);
            setError(null); // Clear error when input changes
          }}
          placeholder='Enter JSON packet (e.g., {"type": "COMMAND", "command": "snap0"})'
          className="packet-input-field"
          rows={3}
          style={{ 
            resize: "vertical", 
            fontFamily: "monospace",
            fontSize: "0.875rem"
          }}
        />
        
        {error && (
          <div className="error-message text-sm" style={{ color: "#e74c3c" }}>
            {error}
          </div>
        )}
        
        <button 
          type="submit" 
          className="packet-send-button"
          disabled={!packetJson.trim()}
        >
          Send Packet
        </button>
      </div>
    </form>
  );
};

export default PacketInput; 