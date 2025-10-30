import { useSendJSON } from "../../hooks/useSendJSON";
import { useState, useRef } from "react";

const createRefreshEvent = (streamType: string, cameraNumber: number) => {
  const event = new CustomEvent('refresh-camera-stream', { 
    detail: { streamType, cameraNumber } 
  });
  window.dispatchEvent(event);
};

const refreshAllStreams = () => {
  const event = new CustomEvent('refresh-all-camera-streams');
  window.dispatchEvent(event);
};

declare global {
  interface HTMLInputElement {
    webkitdirectory: boolean;
    directory: string;
  }
}

const ActionsBox = () => {
  const sendJson = useSendJSON();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedDirectory, setSelectedDirectory] = useState<string>("");
  const directoryInputRef = useRef<HTMLInputElement>(null);

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

  const refreshStream = (streamType: string, cameraNumber: number) => {
    createRefreshEvent(streamType, cameraNumber);
  };

  const handleRefreshAll = () => {
    setIsRefreshing(true);
    refreshAllStreams();
    refreshStream("video_feed", 0);
    refreshStream("video_feed", 1);
    refreshStream("video_feed", 2);
    refreshStream("snapshot_feed", 0);
    refreshStream("snapshot_feed", 1);
    refreshStream("snapshot_feed", 2);
    refreshStream("snapshot_flake_hunted", 0);
    refreshStream("snapshot_flake_hunted", 1);
    refreshStream("snapshot_flake_hunted", 2);
    
    // Reset the refreshing state after a delay
    setTimeout(() => {
      setIsRefreshing(false);
    }, 2000);
  };

  const handleDirectorySelectClick = () => {
    if (directoryInputRef.current) {
      directoryInputRef.current.click();
    }
  };

  const handleDirectoryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    const directory = files[0].webkitRelativePath.split('/')[0];
    setSelectedDirectory(directory);
    event.target.value = '';
  };

  const handleScanFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    sendJson({
      type: "SCAN_FLAKES",
      directory: selectedDirectory
    });
  };

  const handleDrawFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    sendJson({
      type: "DRAW_FLAKES",
      directory: selectedDirectory
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
    </div>
  );
};

export default ActionsBox; 