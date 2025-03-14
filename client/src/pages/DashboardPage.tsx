import CameraDisplay from '../components/CameraDisplay';
import UnifiedLog from '../components/UnifiedLog';
import CommandInput from '../components/CommandInput';
import PacketInput from '../components/PacketInput';
import ActionButtons from '../components/ActionButtons';
import TraceOverBox from '../components/TraceOverBox';
import ScanFlakesBox from '../components/ScanFlakesBox';
import TransferStationCommandInput from '../components/TransferStationCommandInput';

const DashboardPage = () => {
  return (
    <div className="dashboard-page">
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
      
      <div className="dashboard-lower-section">
        <div className="dashboard-boxes">
          <div className="trace-over-container">
            <TraceOverBox />
          </div>
          
          <div className="scan-flakes-container">
            <ScanFlakesBox />
          </div>
        </div>
        
        <div className="dashboard-controls-and-logs">
          <div className="control-section">
            <div className="action-container">
              <h2>Actions</h2>
              <ActionButtons />
            </div>
            
            <div className="input-container">
              <div className="command-input">
                <h2>Command Input</h2>
                <CommandInput />
              </div>
              <div className="ts-command-input">
                <h2>Transfer Station Commands</h2>
                <TransferStationCommandInput />
              </div>
              <div className="packet-input">
                <h2>Packet Input</h2>
                <PacketInput />
              </div>
            </div>
          </div>
          
          <div className="log-section">
            <div className="log-container full-width">
              <h2>System Logs</h2>
              <div className="dashboard-log-wrapper">
                <UnifiedLog />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage; 