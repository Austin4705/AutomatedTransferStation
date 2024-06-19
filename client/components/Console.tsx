/* eslint-disable @typescript-eslint/no-unused-vars */
import useWebSocket from "react-use-websocket";
import ConsoleLog from "./ConsoleLog";
import ConsoleInput from "./ConsoleInput";
import "./Console.css";

export default function Console() {


  return (
    <>
      <div className="flex flex-col h-full">
        <div className="flex-grow">
          <ConsoleLog
            lastJsonMessage={lastJsonMessage}
            readyState={readyState}
          />
        </div>
        <div className="flex-grow-0 flex-shrink-0">
          <ConsoleInput sendJsonMessage={sendJsonMessage} />
        </div>
      </div>
    </>
  );
}
