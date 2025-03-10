import CameraDisplay from '../components/CameraDisplay';
import ActionButtons from '../components/ActionButtons';

const CameraPage = () => {
  return (
    <div className="camera-page">
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
      
      {/* Action Buttons Section */}
      <div className="action-buttons-section mt-6 p-4 bg-gray-100 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Camera Controls</h2>
        <ActionButtons />
      </div>
    </div>
  );
}

export default CameraPage; 