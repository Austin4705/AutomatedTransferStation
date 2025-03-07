import { useEffect } from "react";
import { useRecoilValue } from "recoil";
import "./App.css";
import CameraDisplay from "./components/CameraDisplay";
import ConnectionStatus from "./components/ConnectionStatus";
import CommandLog from "./components/CommandLog";
import ResponseLog from "./components/ResponseLog";
import CommandInput from "./components/CommandInput";
import PacketInput from "./components/PacketInput";
import PositionDisplay from "./components/PositionDisplay";
import ActionButtons from "./components/ActionButtons";
import useSocketJSON from "./hooks/useSocketJSON";
import { jsonStateAtom } from "./state/jsonState";
import { PacketManager } from "./packets/PacketHandler";
import useAppendConsole from "./hooks/useAppendConsole";
import { initializeStore } from "./state/store";

function App() {
  const WS_URL = "ws://127.0.0.1:8765";
  useSocketJSON(WS_URL);
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();

  // Initialize the store with the appendConsole function
  useEffect(() => {
    initializeStore(appendConsole);
  }, [appendConsole]);

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
    <div className="app-container">
      <header className="app-header">
        <h1>Automated Transfer Station</h1>
        <ConnectionStatus />
      </header>
      
      <main className="app-content">
        <div className="camera-section">
          <div className="camera-container primary">
            <h2>Primary Camera</h2>
            <CameraDisplay />
          </div>
          <div className="camera-container secondary">
            <h2>Secondary Camera</h2>
            <CameraDisplay />
          </div>
        </div>
        
        <div className="control-section">
          <div className="position-container">
            <h2>Position Data</h2>
            <PositionDisplay />
          </div>
          
          <div className="action-container">
            <h2>Actions</h2>
            <ActionButtons />
          </div>
          
          <div className="input-container">
            <div className="command-input">
              <h2>Custom Command</h2>
              <CommandInput />
            </div>
            <div className="packet-input">
              <h2>Custom Packet</h2>
              <PacketInput />
            </div>
          </div>
        </div>
        
        <div className="log-section">
          <div className="log-container">
            <h2>Command Log</h2>
            <CommandLog />
          </div>
          <div className="log-container">
            <h2>Response Log</h2>
            <ResponseLog />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
