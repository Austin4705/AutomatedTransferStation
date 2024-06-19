import CameraFeed from "../components/CameraFeed";

import "./App.css";
import ConsoleLog from "../components/ConsoleLog";
import ConsoleInput from "../components/ConsoleInput"
import useWebSocket from "react-use-websocket";

function App() {
  const WS_URL = "ws://127.0.0.1:8765";
  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    WS_URL, {shouldReconnect: (_closeEvent) => true}
  );

  return (
    <>
      <div
        id="grid"
        className="p-4 w-full h-full grid grid-rows-4 grid-cols-10 gap-4"
      >
        <div id="log-container" className="row-start-1 row-span-2 col-span-4">
          <ConsoleLog
            lastJsonMessage={lastJsonMessage}
            readyState={readyState}
          />
        </div>
        <div
          id="camera1-container"
          className="row-start-1 row-span-2 col-span-4 border-2 border-black"
        >
          <CameraFeed id={1} />
        </div>
        <div
          id="camera2-container"
          className="row-start-1 row-span-1 col-span-2 border-2 border-black"
        >
          <CameraFeed id={1} />
        </div>
        <div
          id="camera3-container"
          className="row-start-2 row-span-1 col-span-2 border-2 border-black"
        >
          <CameraFeed id={1} />
        </div>
        <div
          id="controls-container"
          className="row-start-3 row-span-2 col-span-8 h-full grid grid-row-2 grid-col-5 gap-4"
        >
          <div id="subcontrols-container" className="row-span-1 col-span-5 border-2 border-black">
            <ConsoleInput sendJsonMessage={sendJsonMessage} />
          </div>
          <div className="row-span-1 col-span-1 border-2 border-black">
            Choose Axis Button
          </div>
          <div className="border-2 border-black">Controller 1</div>
          <div className="border-2 border-black">Controller 2</div>
          <div className="border-2 border-black">Controller 3</div>
          <div className="border-2 border-black">Controller 4</div>
        </div>
        <div
          id="data-container"
          className="row-start-3 row-span-2 col-span-2 border-2 border-black"
        >
          Data Box
        </div>
      </div>
      {/* <div
          className="m-auto grid gap-20"
          style={{ gridTemplateColumns: "1fr 1fr" }}
        >
          <Console />
          <CameraFeed id={1} />
        </div> */}
    </>
  );
}

export default App;
