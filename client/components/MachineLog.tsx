import { useState, useEffect } from "react"
import Box from '@mui/material/Box';
import useWebSocket, { ReadyState } from "react-use-websocket"
import "./MachineLog.css"
import { TextField, Typography } from "@mui/material";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid"

const readyStateMap = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Open',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
};

export default function MachineLog() {
  const WS_URL = "ws://127.0.0.1:800"
  const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, { shouldReconnect: closeEvent => true, })

  const [userInput, setUserInput] = useState("");
  const [logData, setLogData] = useState<string[]>([]);

  const appendData = (line: string) => {
    setLogData(log => log.concat([line]))
  }

  const sendClientData = (message: string) => {
    if (message.length == 0) return;

    sendMessage(message);
    appendData(`[Client]: ${message}`);
    setUserInput("");
  }

  useEffect(() => {
    if (lastMessage !== null) {
      appendData(`[Log]: ${lastMessage.data}`);
    }
  }, [lastMessage]);

  return <>
    <Box sx={{width:"50vw"}}>
      <Typography>Connection State: {readyStateMap[readyState]}</Typography>

      <Box sx={{
        border: "2px solid black",
        width: "100%",
        height: "500px",
        overflowY: "auto"
      }}>
        {logData.map(log => <Box className="log">{log}</Box>)}
      </Box>

      <Box sx={{
        height: "100px",
        display: "grid",
        gridTemplateColumns: "repeat(6, 2fr)",
        gridTemplateRows: "repeat(6, 50%)",
        gap: "10px"
      }}>
        <Box sx={{ gridColumn: "1 / 5", gridRow: "1 / 2", height: "50px" }}>
          <TextField sx={{width: "100%", height: "100%"}} onChange={e => setUserInput(e.target.value)} value={userInput} variant="outlined" />
        </Box>
        <Box sx={{ gridColumn: "5 / 7", gridRow: "1 / 2", height: "50px" }}>
          <Button sx={{width: "100%", height: "100%"}} onClick={() => sendClientData(userInput)} variant="contained">Send Data</Button>
        </Box>
        <Box sx={{ gridColumn: "1 / 4", gridRow: "2 / 3", height: "50px" }}>
          <Button sx={{width: "100%", height: "100%"}} variant="contained" onClick={() => sendClientData("+5")}>+5</Button>
        </Box>
        <Box sx={{ gridColumn: "4 / 7", gridRow: "2 / 3", height: "50px" }}>
          <Button sx={{width: "100%", height: "100%"}} variant="contained" onClick={() => sendClientData("-5")}>-5</Button>
        </Box>
      </Box>
    </Box>
  </>
} 