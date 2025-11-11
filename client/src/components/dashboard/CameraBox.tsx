import { useEffect, useRef, useCallback } from "react";
import { useRecoilValue, useRecoilState } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { isConsoleMessage } from "../../state/consoleState";
import { connectionStateAtom, cameraStateAtom } from "../../state/appState";

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

const CameraBox = () => {
  const [cameraState, setCameraState] = useRecoilState(cameraStateAtom);
  const connection = useRecoilValue(connectionStateAtom);
  const jsonState = useRecoilValue(jsonStateAtom);

  const imgRef = useRef<HTMLImageElement>(null);
  const imgContainerRef = useRef<HTMLDivElement>(null);
  const baseUrl = `http://${connection.host}:5000/`;

  const { selectedCamera, error, imageKey, isRefreshing, lastSelectedCamera } = cameraState;

  const updateCameraState = useCallback((updates: Partial<typeof cameraState>) => {
    setCameraState(prev => ({ ...prev, ...updates }));
  }, [setCameraState]);

  const refreshStream = useCallback(() => {
    setCameraState(prev => ({ ...prev, isRefreshing: true }));
    const newTimestamp = Date.now();
    setCameraState(prev => ({ ...prev, imageKey: newTimestamp }));

    if (imgRef.current) {
      const isVideoFeed = selectedCamera.startsWith("video_feed");

      if (isVideoFeed) {
        // For video feeds, directly update src to maintain streaming connection
        imgRef.current.src = `${baseUrl}${selectedCamera}?nocache=${newTimestamp}`;
        setTimeout(() => {
          setCameraState(prev => ({ ...prev, error: null, isRefreshing: false }));
        }, 500);
      } else {
        // For snapshots, use preloading to check if image loads successfully
        const preloadImg = new Image();

        const timeoutId = setTimeout(() => {
          setCameraState(prev => ({
            ...prev,
            error: "Camera feed load timeout. The server might be slow or unresponsive.",
            isRefreshing: false
          }));
        }, 5000);

        preloadImg.onload = () => {
          clearTimeout(timeoutId);
          setCameraState(prev => ({ ...prev, error: null, isRefreshing: false }));

          if (imgRef.current) {
            imgRef.current.src = `${baseUrl}${selectedCamera}?nocache=${newTimestamp}`;
          }
        };

        preloadImg.onerror = () => {
          clearTimeout(timeoutId);
          setCameraState(prev => ({
            ...prev,
            error: "Failed to load camera feed. Please check if the camera server is running.",
            isRefreshing: false
          }));
        };

        preloadImg.src = `${baseUrl}${selectedCamera}?nocache=${newTimestamp}`;
      }
    } else {
      setTimeout(() => {
        setCameraState(prev => ({ ...prev, isRefreshing: false }));
      }, 1000);
    }
  }, [baseUrl, selectedCamera, setCameraState]);

  useEffect(() => {
    if (selectedCamera !== lastSelectedCamera) {
      updateCameraState({ lastSelectedCamera: selectedCamera });
      refreshStream();
    }
  }, [selectedCamera, lastSelectedCamera, updateCameraState, refreshStream]);

  useEffect(() => {
    if (
      isConsoleMessage(jsonState.lastJsonMessage) &&
      jsonState.lastJsonMessage.message === "snapped" &&
      (selectedCamera.startsWith("snapshot_feed") || selectedCamera.startsWith("snapshot_flake_hunted"))
    ) {
      refreshStream();
    }
  }, [jsonState.lastJsonMessage, selectedCamera, refreshStream]);

  const handleImageError = () => {
    updateCameraState({
      error: "Failed to load camera feed. Please check if the camera server is running.",
      isRefreshing: false
    });
  };

  const handleImageLoad = () => {
    updateCameraState({ error: null, isRefreshing: false });
  };

  const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    updateCameraState({
      selectedCamera: e.target.value,
      error: null
    });
  };

  useEffect(() => {
    const handleRefreshStream = (event: CustomEvent) => {
      const { streamType, cameraNumber } = event.detail;
      if (selectedCamera === `${streamType}${cameraNumber}`) {
        refreshStream();
      }
    };

    const handleRefreshAllStreams = () => {
      refreshStream();
    };

    window.addEventListener('refresh-camera-stream', handleRefreshStream as EventListener);
    window.addEventListener('refresh-all-camera-streams', handleRefreshAllStreams);

    return () => {
      window.removeEventListener('refresh-camera-stream', handleRefreshStream as EventListener);
      window.removeEventListener('refresh-all-camera-streams', handleRefreshAllStreams);
    };
  }, [selectedCamera, refreshStream]);

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
          disabled={isRefreshing}
          className={`refresh-button ${isRefreshing ? 'bg-gray-300 cursor-not-allowed' : 'bg-gray-200 hover:bg-gray-300'} px-3 py-1 rounded flex items-center`}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      
      <div className="flex-grow overflow-hidden">
        {error ? (
          <div className="error-message text-sm text-center p-4 text-red-500 h-full flex items-center justify-center">
            <div>
              {error}
              <button 
                onClick={refreshStream}
                className="block mx-auto mt-2 text-blue-500 hover:text-blue-700 underline"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div ref={imgContainerRef} className="image-wrapper relative w-full h-full flex items-center justify-center">
            <img 
              ref={imgRef}
              key={`${selectedCamera}-${imageKey}`}
              src={`${baseUrl}${selectedCamera}?nocache=${imageKey}`} 
              alt={`Camera feed: ${selectedCamera}`}
              className={`camera-image ${isRefreshing ? 'opacity-50' : ''}`}
              onError={handleImageError}
              onLoad={handleImageLoad}
              style={{ 
                width: "100%", 
                height: "100%", 
                objectFit: "contain", 
                display: "block"
              }}
            />
            {isRefreshing && (
              <div className="refresh-indicator absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded-full">
                Refreshing...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraBox; 