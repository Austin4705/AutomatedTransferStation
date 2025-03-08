import CameraDisplay from '../components/CameraDisplay';

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
    </div>
  );
}

export default CameraPage; 