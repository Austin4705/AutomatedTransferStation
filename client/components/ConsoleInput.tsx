import { TextField, Button } from "@mui/material";
import Box from "@mui/material/Box";
import { useState } from "react";
import { appendData, consoleState } from "../state/consoleState";
import { useRecoilState } from "recoil";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";
import ConsoleButton from "./ConsoleButton"

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
    
    const new_msg = {
      sender: "Client",
      message: message,
      timestamp: new Date(),
    };

    sendJsonMessage(new_msg);
    appendData(new_msg, setLogData);
    setUserInput("");
  };

  return (
    <Box>
      {/* The Text input */}
      <Box></Box>

      {/* The buttons */}
      <Box
        style={{
          display: "grid",
          gap: "10px",
          gridTemplateColumns: "repeat(3, 1fr)",
        }}
      >
        <ConsoleButton handler={() => sendClientData("+5")}>Add 5</ConsoleButton>
        <ConsoleButton handler={() => sendClientData("-5")}>Subtract 5</ConsoleButton>
      </Box>
    </Box>
  );

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

    </Box>
  );
}
