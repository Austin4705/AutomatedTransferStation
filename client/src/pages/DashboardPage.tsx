import CameraDisplay from '../components/CameraDisplay';
import UnifiedLog from '../components/UnifiedLog';
import CommandInput from '../components/CommandInput';
import PacketInput from '../components/PacketInput';
import ActionButtons from '../components/ActionButtons';
import TraceOverBox from '../components/TraceOverBox';
import ScanFlakesBox from '../components/ScanFlakesBox';
import TransferStationCommandInput from '../components/TransferStationCommandInput';
import { useState } from 'react';

type CameraType = 'primary' | 'secondary';

const DashboardPage = () => {
  const [showBothCameras, setShowBothCameras] = useState(true);
  const [activeCamera, setActiveCamera] = useState<CameraType>('primary');

  const toggleCameraView = () => {
    setShowBothCameras(!showBothCameras);
  };

  const switchToCamera = (camera: CameraType) => {
    setActiveCamera(camera);
    setShowBothCameras(false);
  };

  return (
    <div className="dashboard-page">
      <div className="camera-section" style={{ height: showBothCameras ? '350px' : '450px' }}>
        {showBothCameras ? (
          // Show both cameras side by side
          <>
            <div className="camera-container primary flex flex-col h-full">
              <h2 className="mb-2">Primary Camera</h2>
              <div className="flex-grow overflow-hidden">
                <CameraDisplay />
              </div>
            </div>
            <div className="camera-container secondary flex flex-col h-full">
              <h2 className="mb-2">Secondary Camera</h2>
              <div className="flex-grow overflow-hidden">
                <CameraDisplay />
              </div>
            </div>
          </>
        ) : (
          // Show single camera
          <div className="camera-container flex flex-col h-full" style={{ width: '100%' }}>
            <h2 className="mb-2">{activeCamera === 'primary' ? 'Primary' : 'Secondary'} Camera</h2>
            <div className="flex-grow overflow-hidden">
              <CameraDisplay />
            </div>
          </div>
        )}
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
              <div className="flex justify-between items-center mb-4">
                <h2>Actions</h2>
                <div className="camera-toggle-buttons flex gap-2">
                  {showBothCameras ? (
                    <>
                      <button 
                        onClick={() => switchToCamera('primary')}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                      >
                        Show Only Primary
                      </button>
                      <button 
                        onClick={() => switchToCamera('secondary')}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                      >
                        Show Only Secondary
                      </button>
                    </>
                  ) : (
                    <button 
                      onClick={toggleCameraView}
                      className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                      Show Both Cameras
                    </button>
                  )}
                </div>
              </div>
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