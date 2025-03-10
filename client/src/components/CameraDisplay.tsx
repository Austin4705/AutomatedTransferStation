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
  const imgRef = useRef<HTMLImageElement>(null);
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
    if (imgRef.current) {
      // Store the original src
      const originalSrc = imgRef.current.src.split('?')[0];
      
      // Create a new image element
      const newImg = new Image();
      newImg.onload = () => {
        // Once the new image is loaded, update the src of the displayed image
        if (imgRef.current) {
          imgRef.current.src = newImg.src;
        }
      };
      
      // Force a reload by adding a timestamp
      const timestamp = new Date().getTime();
      newImg.src = `${originalSrc}?t=${timestamp}`;
      
      // Also update the current image with a loading indicator
      imgRef.current.style.opacity = '0.5';
      setTimeout(() => {
        if (imgRef.current) {
          imgRef.current.style.opacity = '1';
        }
      }, 300);
    }
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
    
    // After a short delay to allow state to update, refresh the stream
    setTimeout(() => {
      if (imgRef.current) {
        // Force a reload by adding a timestamp
        const timestamp = new Date().getTime();
        const newSrc = `${baseUrl}${e.target.value}?t=${timestamp}`;
        
        // Create a new image to preload
        const newImg = new Image();
        newImg.onload = () => {
          if (imgRef.current) {
            imgRef.current.src = newImg.src;
            imgRef.current.style.opacity = '1';
          }
        };
        
        // Show loading state
        if (imgRef.current) {
          imgRef.current.style.opacity = '0.5';
        }
        
        // Load the new image
        newImg.src = newSrc;
      }
    }, 50);
  };

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