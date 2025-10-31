import { useSendJSON } from "../../hooks/useSendJSON";
import { useState, useRef, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { positionSettingsAtom } from "../../state/appState";

declare global {
  interface HTMLInputElement {
    webkitdirectory: boolean;
    directory: string;
  }
}

interface Position {
  x: number;
  y: number;
}

interface FlakeCoordinates {
  start: { x: string; y: string };
  end: { x: string; y: string };
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
    start: { x: "0", y: "0" },
    end: { x: "0", y: "0" },
    waferNumber: "",
    imageNumber: ""
  });
  const [keepInputs, setKeepInputs] = useState<boolean>(false);
  const positionSettings = useRecoilValue(positionSettingsAtom);
  const position = positionSettings.currentPosition;

  useEffect(() => {
    if (position) {
      setCurrentPosition({
        x: position.x,
        y: position.y
      });
    }
  }, [position]);

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

  const handleCoordinateChange = (
    corner: "start" | "end",
    axis: "x" | "y",
    value: string
  ) => {
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
  const handleNumberChange = (field: "waferNumber" | "imageNumber", value: string) => {
    if (value !== "" && !/^\d*$/.test(value)) {
      return;
    }

    setFlakeCoordinates(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const copyCurrentPosition = (corner: "start" | "end") => {
    // Format the current position values
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);
    
    setFlakeCoordinates(prev => ({
      ...prev,
      [corner]: {
        x: xValue,
        y: yValue
      }
    }));
  };

  const handleGotoFlake = () => {
    if (!flakeCoordinates.waferNumber || !flakeCoordinates.imageNumber) {
      alert("Please enter both wafer number and image number");
      return;
    }
    
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    const payload = {
      type: "GOTO_WAFER_IMAGE",
      directory: selectedDirectory,
      startXOffset: parseFloat(flakeCoordinates.start.x),
      startYOffset: parseFloat(flakeCoordinates.start.y),
      endXOffset: parseFloat(flakeCoordinates.end.x),
      endYOffset: parseFloat(flakeCoordinates.end.y),
      waferNumber: parseInt(flakeCoordinates.waferNumber),
      imageNumber: parseInt(flakeCoordinates.imageNumber)
    };
    
    sendJson(payload);
    
    if (!keepInputs) {
      setFlakeCoordinates(prev => ({
        ...prev,
        waferNumber: "",
        imageNumber: ""
      }));
    }
  };

  const handleScanFlakes = () => {
    if (!selectedDirectory) {
      alert("Please select a directory first");
      return;
    }
    
    const payload: any = {
      type: "SCAN_FLAKES",
      directory: selectedDirectory
    };

    if (flakeCoordinates.start.x && flakeCoordinates.start.y) {
      payload.start = {
        x: parseFloat(flakeCoordinates.start.x),
        y: parseFloat(flakeCoordinates.start.y)
      };
    }

    if (flakeCoordinates.end.x && flakeCoordinates.end.y) {
      payload.end = {
        x: parseFloat(flakeCoordinates.end.x),
        y: parseFloat(flakeCoordinates.end.y)
      };
    }

    if (flakeCoordinates.waferNumber) {
      payload.waferNumber = parseInt(flakeCoordinates.waferNumber);
    }

    if (flakeCoordinates.imageNumber) {
      payload.imageNumber = parseInt(flakeCoordinates.imageNumber);
    }
    
    sendJson(payload);
    
    if (!keepInputs) {
      setFlakeCoordinates(prev => ({
        ...prev,
        waferNumber: "",
        imageNumber: ""
      }));
    }
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
          <input
            type="file"
            ref={directoryInputRef}
            onChange={handleDirectoryChange}
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

        <div className="flake-coordinates mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Start Offset:</span>
            <input
              type="text"
              value={flakeCoordinates.start.x}
              onChange={(e) => handleCoordinateChange("start", "x", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="X"
            />
            <input
              type="text"
              value={flakeCoordinates.start.y}
              onChange={(e) => handleCoordinateChange("start", "y", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="Y"
            />
            <button
              onClick={() => copyCurrentPosition("start")}
              className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
              title="Copy current position to Start"
            >
              Start
            </button>
          </div>

          <div className="flex items-center space-x-2 mt-2">
            <span className="text-sm font-medium">End Offset:</span>
            <input
              type="text"
              value={flakeCoordinates.end.x}
              onChange={(e) => handleCoordinateChange("end", "x", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="X"
            />
            <input
              type="text"
              value={flakeCoordinates.end.y}
              onChange={(e) => handleCoordinateChange("end", "y", e.target.value)}
              className="p-1 border rounded w-20 text-xs"
              placeholder="Y"
            />
            <button
              onClick={() => copyCurrentPosition("end")}
              className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
              title="Copy current position to End"
            >
              End
            </button>
          </div>
        </div>

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