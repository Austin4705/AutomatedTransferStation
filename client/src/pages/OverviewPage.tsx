import CameraDisplay from "../components/CameraDisplay";
import UnifiedLog from "../components/UnifiedLog";
import CommandInput from "../components/CommandInput";
import PacketInput from "../components/PacketInput";
import ActionButtons from "../components/ActionButtons";
import TraceOverBox from "../components/TraceOverBox";
import TransferStationCommandInput from "../components/TransferStationCommandInput";

const OverviewPage = () => {
  return (
    <div className="overview-page">
      <div className="overview-content">
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
          <div className="action-container">
            <h2>Actions</h2>
            <ActionButtons />
          </div>
          
          <div className="trace-over-container">
            <h2>Trace Over</h2>
            <TraceOverBox />
          </div>
          
          <div className="input-container">
            <div className="command-input mb-4">
              <h2>Command Input</h2>
              <CommandInput />
            </div>
            <div className="ts-command-input mb-4">
              <h2>Transfer Station Commands</h2>
              <TransferStationCommandInput />
            </div>
            <div className="packet-input mb-4">
              <h2>Packet Input</h2>
              <PacketInput />
            </div>
          </div>
        </div>
        
        <div className="log-section">
          <div className="log-container full-width">
            <h2>System Logs</h2>
            <div className="log-wrapper" style={{ 
              height: "250px", 
              overflow: "hidden",
              display: "flex",
              flexDirection: "column" 
            }}>
              <UnifiedLog />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OverviewPage; 