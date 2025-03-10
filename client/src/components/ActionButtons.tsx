import { useSendJSON } from "../hooks/useSendJSON";

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
    // Find all image elements that might match our criteria
    const imgElements = document.querySelectorAll('img') as NodeListOf<HTMLImageElement>;
    
    // Loop through all images to find ones matching our stream type
    imgElements.forEach(img => {
      const src = img.src;
      // Check if this image is for the stream we want to refresh
      if (src.includes(`${streamType}${cameraNumber}`)) {
        // Store the original src without any query parameters
        const originalSrc = src.split('?')[0];
        
        // Create a new image element to preload the refreshed image
        const newImg = new Image();
        newImg.onload = () => {
          // Once the new image is loaded, update the original image
          img.src = newImg.src;
          img.style.opacity = '1';
        };
        
        // Add a visual indicator that we're refreshing
        img.style.opacity = '0.5';
        
        // Force a reload by adding a timestamp
        const timestamp = new Date().getTime();
        newImg.src = `${originalSrc}?t=${timestamp}`;
      }
    });
    
    // Also refresh any images that might be loaded in the future
    // by updating the src attribute of img elements that might not have loaded yet
    setTimeout(() => {
      const newImgElements = document.querySelectorAll('img') as NodeListOf<HTMLImageElement>;
      newImgElements.forEach(img => {
        const src = img.src;
        if (src.includes(`${streamType}${cameraNumber}`) && !src.includes('?t=')) {
          const timestamp = new Date().getTime();
          img.src = `${src}?t=${timestamp}`;
        }
      });
    }, 500);
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
              // Refresh all streams at once
              for (let i = 0; i < 3; i++) {
                refreshStream("video_feed", i);
                refreshStream("snapshot_feed", i);
                refreshStream("snapshot_flake_hunted", i);
              }
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