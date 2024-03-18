import { TextField, Button } from "@mui/material";
import Box from "@mui/material/Box";
import { useState } from "react";
import { appendData, consoleState } from "../state/consoleState";
import { useRecoilState } from "recoil";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";

interface ConsoleInputProps {
  sendJsonMessage: SendJsonMessage;
}

export default function ConsoleInput(props: ConsoleInputProps) {
  const {sendJsonMessage} = props;
  const [userInput, setUserInput] = useState("");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_, setLogData] = useRecoilState(consoleState);

  const sendClientData = (message: string) => {
    if (message.length == 0) return;

    sendJsonMessage(message);
    appendData({
      sender: "Client",
      message: message,
      timestamp: new Date()
    }, setLogData);
    setUserInput("");
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "20%",
        gap: "10px",
      }}
    >
      <Box
        sx={{
          width: "100%",
          height: "50%",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <Box
          sx={{
            width: "67%",
            height: "100%",
            display: "flex",
            alignItems: "center",
          }}
        >
          <TextField
            fullWidth
            onChange={(e) => setUserInput(e.target.value)}
            value={userInput}
            variant="outlined"
          />
        </Box>
        <Button
          sx={{ width: "33%", height: "100%" }}
          onClick={() => sendClientData(userInput)}
          variant="contained"
        >
          Send Data
        </Button>
      </Box>
      <Box
        sx={{
          width: "100%",
          height: "50%",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <Button
          sx={{ width: "50%", height: "100%" }}
          variant="contained"
          onClick={() => sendClientData("+5")}
        >
          +5
        </Button>
        <Button
          sx={{ width: "50%", height: "100%" }}
          variant="contained"
          onClick={() => sendClientData("-5")}
        >
          -5
        </Button>
      </Box>
    </Box>
  );
}
