import { useEffect } from "react";
import { useRecoilValue } from "recoil";
import "./App.css";
import CameraDisplay from "./components/CameraDisplay";
import ConnectionStatus from "./components/ConnectionStatus";
import UnifiedLog from "./components/UnifiedLog";
import CommandInput from "./components/CommandInput";
import PacketInput from "./components/PacketInput";
import PositionDisplay from "./components/PositionDisplay";
import ActionButtons from "./components/ActionButtons";
import TraceOverBox from "./components/TraceOverBox";
import useSocketJSON from "./hooks/useSocketJSON";
import { jsonStateAtom } from "./state/jsonState";
import { PacketManager } from "./packets/PacketHandler";
import HeaderPositionDisplay from "./components/HeaderPositionDisplay";
import TransferStationCommandInput from "./components/TransferStationCommandInput";

function App() {
  const WS_URL = "ws://127.0.0.1:8765";
  useSocketJSON(WS_URL);
  const jsonState = useRecoilValue(jsonStateAtom);

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
        <div className="flex items-center">
          <h1>Automated Transfer Station</h1>
          <HeaderPositionDisplay />
        </div>
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
          {/* Hide the original position display since it's now in the header */}
          {/* <div className="position-container">
            <h2>Position Data</h2>
            <PositionDisplay />
          </div> */}
          
          <div className="action-container">
            <h2>Actions</h2>
            <ActionButtons />
          </div>
          
          <div className="trace-over-container">
            <TraceOverBox />
          </div>
          
          <div className="input-container">
            <div className="command-input">
              <CommandInput />
            </div>
            <div className="ts-command-input">
              <TransferStationCommandInput />
            </div>
            <div className="packet-input">
              <PacketInput />
            </div>
          </div>
        </div>
        
        <div className="log-section">
          <div className="log-container full-width">
            <h2>System Logs</h2>
            <UnifiedLog />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
