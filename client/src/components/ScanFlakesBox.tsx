import { useSendJSON } from "../hooks/useSendJSON";
import { useState, useRef, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { usePositionContext } from "../state/positionContext";

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
  waferNumber: string;
  imageNumber: string;
}

const ScanFlakesBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const [selectedDirectory, setSelectedDirectory] = useState<string>("");
  const directoryInputRef = useRef<HTMLInputElement>(null);
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });
  const [flakeCoordinates, setFlakeCoordinates] = useState<FlakeCoordinates>({
    bottomLeft: { x: "0", y: "0" },
    waferNumber: "",
    imageNumber: ""
  });
  const [keepInputs, setKeepInputs] = useState<boolean>(false);
  const { autoUpdate, pollRate, position } = usePositionContext();

  // Initialize position polling based on autoUpdate setting
  useEffect(() => {
    // Position will be updated automatically through the context
    // and we can just update our local state from the context
    if (position) {
      setCurrentPosition({
        x: position.x,
        y: position.y
      });
    }
  }, [position]);

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

  // Handle wafer and image number changes
  const handleNumberChange = (field: "waferNumber" | "imageNumber", value: string) => {
    // Only allow positive integers
    if (value !== "" && !/^\d*$/.test(value)) {
      return;
    }

    setFlakeCoordinates(prev => ({
      ...prev,
      [field]: value
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

  // Handle goto flake button click
  const handleGotoFlake = () => {
    // Validate required fields
    if (!flakeCoordinates.waferNumber || !flakeCoordinates.imageNumber) {
      alert("Please enter both wafer number and image number");
      return;
    }
    
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    // Send the goto wafer image packet with the coordinates and numbers
    const payload = {
      type: "GOTO_WAFER_IMAGE",
      directory: selectedDirectory,
      bottomLeftXOffset: parseFloat(flakeCoordinates.bottomLeft.x),
      bottomLeftYOffset: parseFloat(flakeCoordinates.bottomLeft.y),
      waferNumber: parseInt(flakeCoordinates.waferNumber),
      imageNumber: parseInt(flakeCoordinates.imageNumber)
    };
    
    sendJson(payload);
    
    // Clear only wafer and image numbers if keepInputs is false
    if (!keepInputs) {
      setFlakeCoordinates(prev => ({
        ...prev,
        waferNumber: "",
        imageNumber: ""
      }));
    }
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

    // Add wafer number if provided
    if (flakeCoordinates.waferNumber) {
      payload.waferNumber = parseInt(flakeCoordinates.waferNumber);
    }

    // Add image number if provided
    if (flakeCoordinates.imageNumber) {
      payload.imageNumber = parseInt(flakeCoordinates.imageNumber);
    }
    
    sendJson(payload);
    
    // Clear inputs if keepInputs is false
    if (!keepInputs) {
      setFlakeCoordinates(prev => ({
        ...prev,
        waferNumber: "",
        imageNumber: ""
      }));
    }
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
          <button
            onClick={handleGotoFlake}
            disabled={!selectedDirectory || !flakeCoordinates.waferNumber || !flakeCoordinates.imageNumber}
            className={`${
              selectedDirectory && flakeCoordinates.waferNumber && flakeCoordinates.imageNumber
                ? "bg-purple-500 hover:bg-purple-600" 
                : "bg-gray-300 cursor-not-allowed"
            } text-white px-3 py-1 rounded`}
          >
            Goto Flake
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

        {/* Wafer and Image Numbers */}
        <div className="wafer-image-numbers mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Wafer Number:</span>
            <input
              type="text"
              value={flakeCoordinates.waferNumber}
              onChange={(e) => handleNumberChange("waferNumber", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="Wafer #"
            />
            <span className="text-sm font-medium ml-2">Image Number:</span>
            <input
              type="text"
              value={flakeCoordinates.imageNumber}
              onChange={(e) => handleNumberChange("imageNumber", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="Image #"
            />
          </div>
        </div>
        
        {/* Keep Inputs Checkbox */}
        <div className="keep-inputs-option mb-2">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={keepInputs}
              onChange={(e) => setKeepInputs(e.target.checked)}
              className="form-checkbox h-4 w-4 text-blue-500"
            />
            <span>Keep inputs after submission</span>
          </label>
        </div>
 
      </div>
    </div>
  );
};

export default ScanFlakesBox; 