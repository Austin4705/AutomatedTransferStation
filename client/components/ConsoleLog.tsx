import { Box, Typography } from "@mui/material";
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
  const {timestamp} = logEntry;
  const formattedTimeStamp = `${timestamp.toLocaleString('en-US')}`;
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
      if (typeof (lastJsonMessage.timestamp) == "string") {
        lastJsonMessage.timestamp = new Date(lastJsonMessage.timestamp)
      }
      appendData(lastJsonMessage, setLogData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastJsonMessage]);

  return (
    <>
      <Typography>Connection State: {readyStateMap[readyState]}</Typography>

      <Box
        sx={{
          border: "2px solid black",
          width: "100%",
          height: "80%",
          overflowY: "auto",
          textAlign: "left"
        }}
      >
        {logData.map((log) => (
          <Box className="log">{entryToString(log)}</Box>
        ))}
      </Box>
    </>
  );
}
