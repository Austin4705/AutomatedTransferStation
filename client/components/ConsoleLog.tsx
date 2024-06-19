import { Typography } from "@mui/material";
import { ReadyState } from "react-use-websocket";
import { useRecoilState } from "recoil";
import {
  appendData,
  consoleMessage,
  consoleState,
  isConsoleMessage,
} from "../state/consoleState";
import { useEffect } from "react";

const readyStateMap = {
  [ReadyState.CONNECTING]: "Connecting",
  [ReadyState.OPEN]: "Open",
  [ReadyState.CLOSING]: "Closing",
  [ReadyState.CLOSED]: "Closed",
  [ReadyState.UNINSTANTIATED]: "Uninstantiated",
};

const entryToString = (logEntry: consoleMessage) => {
  // const {timestamp} = logEntry;
  // const formattedTimeStamp = `${timestamp.toLocaleString('en-US')}`;
  const formattedTimeStamp = "fixme"
  return `[${formattedTimeStamp}] [${logEntry.sender}]: ${logEntry.message}`;
};

interface ConsoleLogProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  lastJsonMessage: consoleMessage | unknown | null;
  readyState: ReadyState;
}

export default function ConsoleLog(props: ConsoleLogProps) {
  const { lastJsonMessage, readyState } = props;
  const [logData, setLogData] = useRecoilState(consoleState);

  useEffect(() => {
    if (isConsoleMessage(lastJsonMessage)) {
      // if (typeof (lastJsonMessage.timestamp) == "string") {
      //   lastJsonMessage.timestamp = new Date(lastJsonMessage.timestamp)
      // }
      appendData(lastJsonMessage, setLogData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastJsonMessage]);

  return (
    <div className="flex flex-col h-full">
      <Typography>Connection State: {readyStateMap[readyState]}</Typography>

      <div className="flex-grow border-2 border-solid border-black overflow-y-auto text-left">
        {logData.map((log) => (
          <div className="log">{entryToString(log)}</div>
        ))}
      </div>
    </div>
  );
}
