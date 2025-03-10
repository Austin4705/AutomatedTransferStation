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
  { id: "snapshot_flake_hunted0", label: "Flake Hunted 0" },
  { id: "snapshot_flake_hunted1", label: "Flake Hunted 1" },
  { id: "snapshot_flake_hunted2", label: "Flake Hunted 2" },
];

const CameraDisplay = () => {
  const [selectedCamera, setSelectedCamera] = useState(CAMERA_OPTIONS[0].id);
  const [error, setError] = useState<string | null>(null);
  const [imageKey, setImageKey] = useState(Date.now()); // Add a key to force re-render
  const imgContainerRef = useRef<HTMLDivElement>(null);
  const jsonState = useRecoilValue(jsonStateAtom);
  const baseUrl = "http://127.0.0.1:5000/";

  // Handle snapshot updates
  useEffect(() => {
    if (
      isConsoleMessage(jsonState.lastJsonMessage) && 
      jsonState.lastJsonMessage.message === "snapped" && 
      (selectedCamera.startsWith("snapshot_feed") || selectedCamera.startsWith("snapshot_flake_hunted"))
    ) {
      // Refresh snapshot image when a new snapshot is taken
      refreshStream();
    }
  }, [jsonState.lastJsonMessage, selectedCamera, baseUrl]);

  // Function to refresh the current stream
  const refreshStream = () => {
    // Force a complete re-render of the image by updating the key
    setImageKey(Date.now());
  };

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
    // Force refresh when changing camera
    setImageKey(Date.now());
  };

  // Add event listeners for refresh events
  useEffect(() => {
    // Handler for refreshing specific streams
    const handleRefreshStream = (event: CustomEvent) => {
      const { streamType, cameraNumber } = event.detail;
      // Check if this is the stream we're currently displaying
      if (selectedCamera === `${streamType}${cameraNumber}`) {
        refreshStream();
      }
    };

    // Handler for refreshing all streams
    const handleRefreshAllStreams = () => {
      refreshStream();
    };

    // Add event listeners
    window.addEventListener('refresh-camera-stream', handleRefreshStream as EventListener);
    window.addEventListener('refresh-all-camera-streams', handleRefreshAllStreams);

    // Clean up event listeners
    return () => {
      window.removeEventListener('refresh-camera-stream', handleRefreshStream as EventListener);
      window.removeEventListener('refresh-all-camera-streams', handleRefreshAllStreams);
    };
  }, [selectedCamera]); // Re-add listeners if selectedCamera changes

  return (
    <div className="camera-display h-full flex flex-col">
      <div className="camera-controls flex justify-between items-center mb-2">
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
        
        <button 
          onClick={refreshStream}
          className="refresh-button bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>
      
      <div className="camera-image-container flex-grow bg-gray-100 rounded flex items-center justify-center" ref={imgContainerRef}>
        {error ? (
          <div className="error-message text-sm text-center p-4 text-red-500">
            {error}
          </div>
        ) : (
          <img 
            key={imageKey} // This forces React to recreate the element when imageKey changes
            src={`${baseUrl}${selectedCamera}?t=${imageKey}`} 
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