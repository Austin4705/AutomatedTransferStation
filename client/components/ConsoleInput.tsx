import React from "react";
import { useState } from "react";
import { appendData, consoleState } from "../state/consoleState";
import { useRecoilState } from "recoil";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";

interface ConsoleInputProps {
  sendJsonMessage: SendJsonMessage;
}

export default function ConsoleInput(props: ConsoleInputProps) {
  const { sendJsonMessage } = props;
  const [userInput, setUserInput] = useState("");
  const [, setLogData] = useRecoilState(consoleState);

  const sendClientData = (message: string) => {
    if (message.length == 0) return;

    const new_msg = {
      sender: "Client",
      message: message
    };

    sendJsonMessage(new_msg);
    appendData(new_msg, setLogData);
    setUserInput("");
  };

  const handleKeyDown = (event: any) => {
    if (event.key === 'Enter') {
      sendClientData(userInput)
    }
  }

  return (
    <div className="p-2 flex gap-2">
      <input className="border-purple-200 border-2 rounded" onKeyDown={handleKeyDown} onChange={e => setUserInput(e.target.value)} value={userInput} placeholder="Manual input"></input>
      <button className="bg-gray-200 rounded" onClick={() => sendClientData(userInput)}>Submit</button>
    </div>
  );
}
