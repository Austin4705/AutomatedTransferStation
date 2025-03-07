import { Typography } from "@mui/material";
import { ReadyState } from "react-use-websocket";
import { useRecoilValue } from "recoil";
import {
  consoleMessage,
  consoleStateAtom,
  isConsoleMessage,
} from "../state/consoleState";
import { useEffect } from "react";
import { jsonStateAtom } from "../state/jsonState";
import useAppendConsole from "../hooks/useAppendConsole";
import { PacketManager } from "../packets/PacketHandler";
import { PacketHandlers } from "../packets/PacketHandlers";

const readyStateMap = {
  [ReadyState.CONNECTING]: "Connecting",
  [ReadyState.OPEN]: "Open",
  [ReadyState.CLOSING]: "Closing",
  [ReadyState.CLOSED]: "Closed",
  [ReadyState.UNINSTANTIATED]: "Uninstantiated",
};

const entryToString = (logEntry: consoleMessage) => {
  const timestamp = new Date().toLocaleString('en-US');
  return `[${timestamp}] [${logEntry.sender}]: ${logEntry.message}`;
};

export default function ConsoleLog() {
  const logData = useRecoilValue(consoleStateAtom);
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendData = useAppendConsole();

  useEffect(() => {
    // Initialize packet system
    PacketManager.initialize().then(() => {
      console.log("Packet system initialized");
    });
  }, []);

  useEffect(() => {
    if (jsonState.lastJsonMessage) {
      console.log("Received websocket message:", jsonState.lastJsonMessage);
      PacketManager.handlePacket(jsonState.lastJsonMessage as any);
    }
  }, [jsonState.lastJsonMessage]);

  return (
    <div className="flex flex-col h-full">
      <Typography>
        Connection State: {readyStateMap[jsonState.readyState]}
      </Typography>

      <div className="flex-grow border-2 border-solid border-black overflow-y-auto text-left">
        {logData.map((log) => (
          <div className="log">{entryToString(log)}</div>
        ))}
      </div>
    </div>
  );
}
