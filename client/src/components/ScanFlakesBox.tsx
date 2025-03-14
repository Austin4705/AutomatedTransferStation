import { useSendJSON } from "../hooks/useSendJSON";
import { useState, useRef, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";

// Extend the HTMLInputElement interface to include webkitdirectory
declare global {
  interface HTMLInputElement {
    webkitdirectory: boolean;
    directory: string;
  }
}

// Interface for position
interface Position {
  x: number;
  y: number;
}

// Interface for flake coordinates
interface FlakeCoordinates {
  bottomLeft: { x: string; y: string };
}

const ScanFlakesBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const [selectedDirectory, setSelectedDirectory] = useState<string>("");
  const directoryInputRef = useRef<HTMLInputElement>(null);
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });
  const [flakeCoordinates, setFlakeCoordinates] = useState<FlakeCoordinates>({
    bottomLeft: { x: "", y: "" }
  });

  // Listen for position responses from the server
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;
    
    // Track current position from any position messages
    if (message.type === "POSITION" || message.type === "RESPONSE_POSITION") {
      if (typeof message.x === 'number' && typeof message.y === 'number') {
        setCurrentPosition({
          x: message.x,
          y: message.y
        });
      }
    }
  }, [jsonState.lastJsonMessage]);

  // Request current position from the server
  const requestCurrentPosition = () => {
    sendJson({
      type: "REQUEST_POSITION"
    });
  };

  // Initialize by requesting the current position
  useEffect(() => {
    requestCurrentPosition();
    
    // Set up a timer to periodically request the position
    const intervalId = setInterval(requestCurrentPosition, 5000);
    
    // Clean up the interval when the component unmounts
    return () => clearInterval(intervalId);
  }, []);

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

  // Handle coordinate change
  const handleCoordinateChange = (
    corner: "bottomLeft",
    axis: "x" | "y",
    value: string
  ) => {
    // Only allow numbers and decimal points
    if (value !== "" && !/^-?\d*\.?\d*$/.test(value)) {
      return;
    }

    setFlakeCoordinates(prev => ({
      ...prev,
      [corner]: {
        ...prev[corner],
        [axis]: value
      }
    }));
  };

  // Copy current position to bottom left coordinates
  const copyCurrentPosition = () => {
    // Format the current position values
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);
    
    // Update the bottom left coordinates with the current position
    setFlakeCoordinates(prev => ({
      ...prev,
      bottomLeft: {
        x: xValue,
        y: yValue
      }
    }));
  };

  // Handle scan flakes button click
  const handleScanFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    // Send the scan flakes packet with the selected directory and coordinates if provided
    const payload: any = {
      type: "SCAN_FLAKES",
      directory: selectedDirectory
    };

    // Add coordinates if they are provided
    if (flakeCoordinates.bottomLeft.x && flakeCoordinates.bottomLeft.y) {
      payload.bottomLeft = {
        x: parseFloat(flakeCoordinates.bottomLeft.x),
        y: parseFloat(flakeCoordinates.bottomLeft.y)
      };
    }
    
    sendJson(payload);
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

        {/* Flake Coordinates */}
        <div className="flake-coordinates mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Bottom Left Offset:</span>
            <input
              type="text"
              value={flakeCoordinates.bottomLeft.x}
              onChange={(e) => handleCoordinateChange("bottomLeft", "x", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="X"
            />
            <input
              type="text"
              value={flakeCoordinates.bottomLeft.y}
              onChange={(e) => handleCoordinateChange("bottomLeft", "y", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="Y"
            />
            <button
              onClick={copyCurrentPosition}
              className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
              title="Copy current position to Bottom Left"
            >
              BL
            </button>
          </div>
        </div>
 
      </div>
    </div>
  );
};

export default ScanFlakesBox; 