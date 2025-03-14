import { useSendJSON } from "../hooks/useSendJSON";
import { useState, useRef } from "react";

// Extend the HTMLInputElement interface to include webkitdirectory
declare global {
  interface HTMLInputElement {
    webkitdirectory: boolean;
    directory: string;
  }
}

const ScanFlakesBox = () => {
  const sendJson = useSendJSON();
  const [selectedDirectory, setSelectedDirectory] = useState<string>("");
  const directoryInputRef = useRef<HTMLInputElement>(null);

  // Trigger directory input click
  const handleDirectorySelectClick = () => {
    if (directoryInputRef.current) {
      directoryInputRef.current.click();
    }
  };

  // Handle directory selection
  const handleDirectoryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    // Get the directory path
    // Note: Due to security restrictions, we can only get the file name, not the full path
    // We'll use webkitRelativePath to get the directory structure
    const directory = files[0].webkitRelativePath.split('/')[0];
    setSelectedDirectory(directory);
    
    // Reset the file input so the same directory can be selected again
    event.target.value = '';
  };

  // Handle scan flakes button click
  const handleScanFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    // Send the scan flakes packet with the selected directory
    sendJson({
      type: "SCAN_FLAKES",
      directory: selectedDirectory
    });
  };

  // Handle draw flakes button click
  const handleDrawFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    // Send the draw flakes packet with the selected directory
    sendJson({
      type: "DRAW_FLAKES",
      directory: selectedDirectory
    });
  };

  return (
    <div className="scan-flakes-box p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-4">Scan Flakes</h2>
      
      <div className="flex flex-col space-y-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleDirectorySelectClick}
            className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded"
          >
            Select Directory
          </button>
          <span className="text-sm text-gray-600 truncate max-w-xs">
            {selectedDirectory ? selectedDirectory : "No directory selected"}
          </span>
          {/* Hidden directory input */}
          <input
            type="file"
            ref={directoryInputRef}
            onChange={handleDirectoryChange}
            // Use data attributes to avoid TypeScript errors
            // @ts-ignore
            webkitdirectory=""
            directory=""
            className="hidden"
          />
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handleScanFlakes}
            disabled={!selectedDirectory}
            className={`${
              selectedDirectory 
                ? "bg-green-500 hover:bg-green-600" 
                : "bg-gray-300 cursor-not-allowed"
            } text-white px-3 py-1 rounded`}
          >
            Scan Flakes
          </button>
          <button
            onClick={handleDrawFlakes}
            disabled={!selectedDirectory}
            className={`${
              selectedDirectory 
                ? "bg-orange-500 hover:bg-orange-600" 
                : "bg-gray-300 cursor-not-allowed"
            } text-white px-3 py-1 rounded`}
          >
            Draw Flakes
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScanFlakesBox; 