import { useState, useEffect, useRef } from "react";
import { isConsoleMessage } from "../state/consoleState";
import { jsonStateAtom } from "../state/jsonState";
import { useRecoilValue } from "recoil";

export default function CameraFeed(props: any) {
    const [imageKey, setImageKey] = useState(Date.now());
    const [error, setError] = useState<string | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const baseUrl: string = "http://127.0.0.1:5000/";
    const cameraId = props.id;
    const imgRef = useRef<HTMLImageElement>(null);

    const jsonState = useRecoilValue(jsonStateAtom);
    
    // Handle snapshot updates
    useEffect(() => {
      if(isConsoleMessage(jsonState.lastJsonMessage) && 
         jsonState.lastJsonMessage.message === "snapped" && 
         cameraId.startsWith("s")) {
        refreshStream();
      }
    }, [jsonState.lastJsonMessage, cameraId]);

    // Function to refresh the camera stream
    const refreshStream = () => {
      setIsRefreshing(true);
      
      // Generate a new timestamp for cache busting
      const newTimestamp = Date.now();
      setImageKey(newTimestamp);
      
      // If we have a reference to the image element, we can also directly manipulate it
      if (imgRef.current) {
        // Create a new image element to preload the fresh image
        const preloadImg = new Image();
        
        // Set a timeout to detect if the image load is taking too long
        const timeoutId = setTimeout(() => {
          setError("Camera feed load timeout. The server might be slow or unresponsive.");
          setIsRefreshing(false);
        }, 5000);
        
        // Set up event handlers for the preload image
        preloadImg.onload = () => {
          clearTimeout(timeoutId);
          setError(null);
          setIsRefreshing(false);
          
          // Once preloaded successfully, update the src of the actual image in the DOM
          if (imgRef.current) {
            imgRef.current.src = preloadImg.src;
          }
        };
        
        preloadImg.onerror = () => {
          clearTimeout(timeoutId);
          setError("Failed to load camera feed. Please check if the camera server is running.");
          setIsRefreshing(false);
        };
        
        // Set the new source with a cache-busting parameter
        preloadImg.src = `${baseUrl}${cameraId}?nocache=${newTimestamp}`;
      }
    };

    // Add event listeners for refresh events
    useEffect(() => {
      // Handler for refreshing specific streams
      const handleRefreshStream = (event: CustomEvent) => {
        const { streamType, cameraNumber } = event.detail;
        // Check if this is the stream we're currently displaying
        if (cameraId === `${streamType}${cameraNumber}`) {
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
    }, [cameraId]); // Re-add listeners if cameraId changes

    // Handle image loading errors
    const handleImageError = () => {
      setError("Failed to load camera feed. Please check if the camera server is running.");
      setIsRefreshing(false);
    };

    // Handle image load success
    const handleImageLoad = () => {
      setError(null);
      setIsRefreshing(false);
    };

    return (
      <div className="camera-feed-container relative w-full h-full">
        {error ? (
          <div className="error-message absolute inset-0 flex items-center justify-center bg-gray-100 text-sm text-center p-4 text-red-500">
            {error}
            <button 
              onClick={refreshStream}
              className="block absolute bottom-4 left-1/2 transform -translate-x-1/2 text-blue-500 hover:text-blue-700 underline"
            >
              Try Again
            </button>
          </div>
        ) : (
          <img 
            ref={imgRef}
            key={imageKey} 
            src={`${baseUrl}${cameraId}?nocache=${imageKey}`} 
            alt={`Camera feed: ${cameraId}`}
            className={`object-scale-down w-full h-full ${isRefreshing ? 'opacity-50' : ''}`}
            onError={handleImageError}
            onLoad={handleImageLoad}
          />
        )}
        
        {isRefreshing && !error && (
          <div className="refresh-indicator absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded-full">
            Refreshing...
          </div>
        )}
      </div>
    );
}