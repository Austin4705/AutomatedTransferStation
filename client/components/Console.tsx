/* eslint-disable @typescript-eslint/no-unused-vars */
import Box from "@mui/material/Box";
import useWebSocket from "react-use-websocket";
import ConsoleLog from "./ConsoleLog";
import ConsoleInput from "./ConsoleInput";
import "./Console.css";

export default function MachineLog() {
  const WS_URL = "ws://127.0.0.1:8765";
  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(WS_URL, {
    shouldReconnect: (_closeEvent) => true,
  });

  return (
    <>
      <Box sx={{ width: "50vw", height: "700px" }}>
        <ConsoleLog lastJsonMessage={lastJsonMessage} readyState={readyState} />
        <ConsoleInput sendJsonMessage={sendJsonMessage} />
      </Box>
    </>
  );
}
