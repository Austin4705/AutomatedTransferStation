import React from "react";
import { useState } from "react";
import useSendJSON from "../hooks/useSendJSON"

export default function ConsoleInput() {
  const [userInput, setUserInput] = useState("");
  const sendJSONData = useSendJSON();

  const sendClientData = (message: string) => {
    sendJSONData(message);
    setUserInput("");
  };

  return (
    <div className="p-2 flex gap-2">
      <input
        className="border-purple-200 border-2 rounded"
        onKeyDown={e => {e.key === "Enter" && sendClientData(userInput)}}
        onChange={(e) => setUserInput(e.target.value)}
        value={userInput}
        placeholder="Manual input"
      />
      <button
        className="bg-gray-200 rounded"
        onClick={() => sendClientData(userInput)}
      >
        Submit
      </button>
    </div>
  );
}
