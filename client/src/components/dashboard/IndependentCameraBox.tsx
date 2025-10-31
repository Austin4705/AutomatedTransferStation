import { useEffect, useRef, useState } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { isConsoleMessage } from "../../state/consoleState";
import { connectionStateAtom } from "../../state/appState";
import { useSendJSON } from "../../hooks/useSendJSON";

interface IndependentCameraBoxProps {
  cameraId: string; // Unique ID for this camera widget (e.g., "camera-1", "camera-2")
  defaultCamera?: number; // Default camera number (0, 1, or 2)
}

type FeedType = 'video' | 'snapshot' | 'flake_hunted';

const IndependentCameraBox = ({ cameraId, defaultCamera = 0 }: IndependentCameraBoxProps) => {
  const connection = useRecoilValue(connectionStateAtom);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Local state for this camera widget only
  const [cameraNumber, setCameraNumber] = useState<number>(defaultCamera);
  const [feedType, setFeedType] = useState<FeedType>('video');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageKey, setImageKey] = useState(Date.now());

  const imgRef = useRef<HTMLImageElement>(null);
  const baseUrl = `http://${connection.host}:5000/`;

  // Construct the feed URL based on current selections
  const getFeedUrl = () => {
    let feedPath = '';
    switch (feedType) {
      case 'video':
        feedPath = `video_feed${cameraNumber}`;
        break;
      case 'snapshot':
        feedPath = `snapshot_feed${cameraNumber}`;
        break;
      case 'flake_hunted':
        feedPath = `snapshot_flake_hunted${cameraNumber}`;
        break;
    }
    return feedPath;
  };

  const currentFeed = getFeedUrl();

  const refreshStream = () => {
    setIsRefreshing(true);
    setError(null);

    // Use both timestamp and random number for aggressive cache busting
    const newTimestamp = Date.now();
    const randomComponent = Math.random().toString(36).substring(7);
    const cacheKey = `${newTimestamp}_${randomComponent}`;
    setImageKey(newTimestamp);

    // Force immediate update of the current feed URL
    const feedToLoad = getFeedUrl();
    const urlToLoad = `${baseUrl}${feedToLoad}?nocache=${cacheKey}`;

    if (imgRef.current) {
      // Clear the current image source to force reload
      imgRef.current.src = '';

      const preloadImg = new Image();

      const timeoutId = setTimeout(() => {
        setError("Camera feed load timeout. The server might be slow or unresponsive.");
        setIsRefreshing(false);
      }, 5000);

      preloadImg.onload = () => {
        clearTimeout(timeoutId);
        setError(null);
        setIsRefreshing(false);

        if (imgRef.current) {
          imgRef.current.src = urlToLoad;
        }
      };

      preloadImg.onerror = () => {
        clearTimeout(timeoutId);
        setError("Failed to load camera feed. Please check if the camera server is running.");
        setIsRefreshing(false);
      };

      preloadImg.src = urlToLoad;
    } else {
      setTimeout(() => {
        setIsRefreshing(false);
      }, 1000);
    }
  };

  // Refresh when feed changes
  useEffect(() => {
    refreshStream();
  }, [cameraNumber, feedType, connection.host]);

  // Auto-refresh snapshot/flake_hunted feeds when snap message received
  useEffect(() => {
    if (
      isConsoleMessage(jsonState.lastJsonMessage) &&
      jsonState.lastJsonMessage.message === "snapped" &&
      (feedType === 'snapshot' || feedType === 'flake_hunted')
    ) {
      refreshStream();
    }
  }, [jsonState.lastJsonMessage, feedType]);

  const handleImageError = () => {
    setError("Failed to load camera feed. Please check if the camera server is running.");
    setIsRefreshing(false);
  };

  const handleImageLoad = () => {
    setError(null);
    setIsRefreshing(false);
  };

  const handleSnap = () => {
    sendJson({
      type: "SNAP_SHOT",
      camera: cameraNumber
    });
  };

  const handleSnapFlakeHunted = () => {
    sendJson({
      type: "SNAP_SHOT_FLAKE_HUNTED",
      camera: cameraNumber
    });
  };

  return (
    <div className="camera-display h-full flex flex-col p-3">
      {/* Camera Feed Display */}
      <div className="flex-grow overflow-hidden mb-2 bg-gray-100 rounded">
        {error ? (
          <div className="error-message text-sm text-center p-4 text-red-500 h-full flex items-center justify-center">
            <div>
              {error}
              <button
                onClick={refreshStream}
                className="block mx-auto mt-2 text-blue-500 hover:text-blue-700 underline text-xs"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : (
          <div className="image-wrapper relative w-full h-full flex items-center justify-center">
            <img
              ref={imgRef}
              key={`${cameraId}-${currentFeed}-${imageKey}`}
              src={`${baseUrl}${currentFeed}?t=${imageKey}`}
              alt={`Camera ${cameraNumber} - ${feedType}`}
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

      {/* All Controls at Bottom */}
      <div className="controls-container space-y-2">
        {/* Camera Selection */}
        <div className="camera-controls">
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Camera
          </label>
          <div className="flex gap-1">
            {[0, 1, 2].map((num) => (
              <button
                key={num}
                onClick={() => setCameraNumber(num)}
                className={`flex-1 px-2 py-1 text-xs rounded transition-colors ${
                  cameraNumber === num
                    ? 'bg-blue-500 text-white font-semibold'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Cam {num}
              </button>
            ))}
          </div>
        </div>

        {/* Feed Type Selection */}
        <div className="feed-type-controls">
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Feed Type
          </label>
          <div className="flex gap-1">
            <button
              onClick={() => setFeedType('video')}
              className={`flex-1 px-2 py-1 text-xs rounded transition-colors ${
                feedType === 'video'
                  ? 'bg-green-500 text-white font-semibold'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Video
            </button>
            <button
              onClick={() => setFeedType('snapshot')}
              className={`flex-1 px-2 py-1 text-xs rounded transition-colors ${
                feedType === 'snapshot'
                  ? 'bg-green-500 text-white font-semibold'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Snap
            </button>
            <button
              onClick={() => setFeedType('flake_hunted')}
              className={`flex-1 px-2 py-1 text-xs rounded transition-colors ${
                feedType === 'flake_hunted'
                  ? 'bg-green-500 text-white font-semibold'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Flake
            </button>
          </div>
        </div>

        {/* Action Buttons Row */}
        <div className="action-buttons flex gap-1">
          <button
            onClick={handleSnap}
            className="flex-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors font-medium"
          >
            Take Snap
          </button>
          <button
            onClick={handleSnapFlakeHunted}
            className="flex-1 px-2 py-1 text-xs bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors font-medium"
          >
            Flake Snap
          </button>
          <button
            onClick={refreshStream}
            disabled={isRefreshing}
            className={`flex-1 px-2 py-1 text-xs rounded transition-colors flex items-center justify-center ${
              isRefreshing ? 'bg-gray-300 cursor-not-allowed' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`h-3 w-3 mr-1 ${isRefreshing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {isRefreshing ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default IndependentCameraBox;
