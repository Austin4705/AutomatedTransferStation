import { useSendJSON } from "../hooks/useSendJSON";

// Create a global event for refreshing streams
// This allows components to communicate without direct props
const createRefreshEvent = (streamType: string, cameraNumber: number) => {
  const event = new CustomEvent('refresh-camera-stream', { 
    detail: { streamType, cameraNumber } 
  });
  window.dispatchEvent(event);
};

// Global function to refresh all streams
const refreshAllStreams = () => {
  const event = new CustomEvent('refresh-all-camera-streams');
  window.dispatchEvent(event);
};

const ActionButtons = () => {
  const sendJson = useSendJSON();

  const handleSnap = (snapNumber: number) => {
    sendJson({
      type: "SNAP_SHOT",
      camera: snapNumber
    });
  };

  const handleSnapFlakeHunted = (snapNumber: number) => {
    sendJson({
      type: "SNAP_SHOT_FLAKE_HUNTED",
      camera: snapNumber
    });
  };

  // Function to refresh a specific camera stream
  const refreshStream = (streamType: string, cameraNumber: number) => {
    // Dispatch a custom event that CameraDisplay will listen for
    createRefreshEvent(streamType, cameraNumber);
    
    // Also try the direct DOM approach as a fallback
    const imgElements = document.querySelectorAll('img') as NodeListOf<HTMLImageElement>;
    imgElements.forEach(img => {
      const src = img.src;
      if (src.includes(`${streamType}${cameraNumber}`)) {
        // Force a complete reload by recreating the element
        const parent = img.parentNode;
        if (parent) {
          const newImg = document.createElement('img');
          // Copy all attributes
          Array.from(img.attributes).forEach(attr => {
            newImg.setAttribute(attr.name, attr.value);
          });
          // Set a new src with timestamp
          newImg.src = `${src.split('?')[0]}?t=${Date.now()}`;
          // Replace the old image
          parent.replaceChild(newImg, img);
        }
      }
    });
  };

  return (
    <div className="action-buttons space-y-4">
      <div className="button-section">
        <h3 className="text-sm font-medium mb-2">Regular Snapshots</h3>
        <div className="button-group flex flex-wrap gap-2">
          <button 
            onClick={() => handleSnap(0)}
            className="snap-button bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
          >
            Snap 0
          </button>
          
          <button 
            onClick={() => handleSnap(1)}
            className="snap-button bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
          >
            Snap 1
          </button>
          
          <button 
            onClick={() => handleSnap(2)}
            className="snap-button bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
          >
            Snap 2
          </button>
        </div>
      </div>

      <div className="button-section">
        <h3 className="text-sm font-medium mb-2">Flake Hunt Snapshots</h3>
        <div className="button-group flex flex-wrap gap-2">
          <button 
            onClick={() => handleSnapFlakeHunted(0)}
            className="snap-button bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded"
          >
            Flake Hunt 0
          </button>
          
          <button 
            onClick={() => handleSnapFlakeHunted(1)}
            className="snap-button bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded"
          >
            Flake Hunt 1
          </button>
          
          <button 
            onClick={() => handleSnapFlakeHunted(2)}
            className="snap-button bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded"
          >
            Flake Hunt 2
          </button>
        </div>
      </div>

      <div className="button-section">
        <h3 className="text-sm font-medium mb-2">Refresh Streams</h3>
        <div className="button-group flex flex-wrap gap-2">
          <button 
            onClick={() => {
              // Most direct approach - reload the page
              window.location.reload();
            }}
            className="refresh-button bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh ALL Streams
          </button>
          
          <button 
            onClick={() => {
              refreshStream("video_feed", 0);
              refreshStream("video_feed", 1);
              refreshStream("video_feed", 2);
            }}
            className="refresh-button bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Video Feeds
          </button>
          
          <button 
            onClick={() => {
              refreshStream("snapshot_feed", 0);
              refreshStream("snapshot_feed", 1);
              refreshStream("snapshot_feed", 2);
            }}
            className="refresh-button bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Snapshots
          </button>
          
          <button 
            onClick={() => {
              refreshStream("snapshot_flake_hunted", 0);
              refreshStream("snapshot_flake_hunted", 1);
              refreshStream("snapshot_flake_hunted", 2);
            }}
            className="refresh-button bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Flake Hunted
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionButtons; 