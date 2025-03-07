import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { isConsoleMessage } from "../state/consoleState";

const CAMERA_OPTIONS = [
  { id: "video_feed0", label: "Main Camera" },
  { id: "video_feed1", label: "Secondary Camera" },
  { id: "video_feed2", label: "Tertiary Camera" },
  { id: "snapshot_feed0", label: "Snapshot 0" },
  { id: "snapshot_feed1", label: "Snapshot 1" },
  { id: "snapshot_feed2", label: "Snapshot 2" },
];

const CameraDisplay = () => {
  const [selectedCamera, setSelectedCamera] = useState(CAMERA_OPTIONS[0].id);
  const [error, setError] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const jsonState = useRecoilValue(jsonStateAtom);
  const baseUrl = "http://127.0.0.1:5000/";

  // Handle snapshot updates
  useEffect(() => {
    if (
      isConsoleMessage(jsonState.lastJsonMessage) && 
      jsonState.lastJsonMessage.message === "snapped" && 
      selectedCamera.startsWith("snapshot")
    ) {
      // Refresh snapshot image when a new snapshot is taken
      if (imgRef.current) {
        const timestamp = new Date().getTime();
        imgRef.current.src = `${baseUrl}${selectedCamera}?t=${timestamp}`;
      }
    }
  }, [jsonState.lastJsonMessage, selectedCamera, baseUrl]);

  // Handle image loading errors
  const handleImageError = () => {
    setError("Failed to load camera feed. Please check if the camera server is running.");
  };

  // Handle image load success
  const handleImageLoad = () => {
    setError(null);
  };

  const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCamera(e.target.value);
    setError(null); // Reset error when changing camera
  };

  return (
    <div className="camera-display h-full flex flex-col">
      <div className="camera-select-container mb-2">
        <select 
          value={selectedCamera} 
          onChange={handleCameraChange}
          className="camera-select"
        >
          {CAMERA_OPTIONS.map((camera) => (
            <option key={camera.id} value={camera.id}>
              {camera.label}
            </option>
          ))}
        </select>
      </div>
      
      <div className="camera-image-container flex-grow bg-gray-100 rounded flex items-center justify-center">
        {error ? (
          <div className="error-message text-sm text-center p-4 text-red-500">
            {error}
          </div>
        ) : (
          <img 
            ref={imgRef}
            src={`${baseUrl}${selectedCamera}`} 
            alt={`Camera feed: ${selectedCamera}`}
            className="camera-image"
            onError={handleImageError}
            onLoad={handleImageLoad}
            style={{ 
              maxWidth: "100%", 
              maxHeight: "100%", 
              objectFit: "contain",
              display: "block"
            }}
          />
        )}
      </div>
    </div>
  );
};

export default CameraDisplay; 