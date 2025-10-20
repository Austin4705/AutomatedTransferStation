import CameraDisplay from '../components/CameraDisplay';
import ActionButtons from '../components/ActionButtons';
import { useState } from 'react';

type CameraType = 'primary' | 'secondary';

const CameraPage = () => {
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
    <div className="camera-page">
      <div className="camera-section" style={{ height: showBothCameras ? 'calc(100vh - 230px)' : 'calc(100vh - 230px)' }}>
        <h2 className="text-xl font-semibold mb-4">Camera View</h2>

        {showBothCameras ? (
          // Show both cameras side by side
          <div className="grid grid-cols-2 gap-4 h-full">
            <div className="camera-container primary p-3 border rounded-lg flex flex-col h-full">
              <h2 className="mb-2">Primary Camera</h2>
              <div className="flex-grow overflow-hidden">
                <CameraDisplay />
              </div>
            </div>
            
            <div className="camera-container secondary p-3 border rounded-lg flex flex-col h-full">
              <h2 className="mb-2">Secondary Camera</h2>
              <div className="flex-grow overflow-hidden">
                <CameraDisplay />
              </div>
            </div>
          </div>
        ) : (
          // Show single camera
          <div className="camera-container p-3 border rounded-lg flex flex-col h-full">
            <h2 className="mb-2">{activeCamera === 'primary' ? 'Primary' : 'Secondary'} Camera</h2>
            <div className="flex-grow overflow-hidden">
              <CameraDisplay />
            </div>
          </div>
        )}
      </div>
      
      {/* Action Buttons Section */}
      <div className="action-buttons-section mt-6 p-4 bg-gray-100 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Camera Controls</h2>
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
    </div>
  );
}

export default CameraPage; 