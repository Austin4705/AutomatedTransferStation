import { useSendJSON } from "../hooks/useSendJSON";
import { useState, useEffect, useRef, ChangeEvent } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";

// Interface for flake coordinates
interface FlakeCoordinates {
  id: number;
  topRight: { x: string; y: string };
  bottomLeft: { x: string; y: string };
}

// Interface for position data
interface Position {
  x: number;
  y: number;
  [key: string]: number;
}

// Interface for tracking which coordinate to update with position data
interface PositionUpdateTarget {
  flakeId: number;
  corner: "topRight" | "bottomLeft" | "both";
}

// Interface for trace over result
interface TraceOverResult {
  success: boolean;
  message: string;
  flakeCount?: number;
}

const TraceOverBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const [flakeCount, setFlakeCount] = useState<number>(1);
  const [flakeCoordinates, setFlakeCoordinates] = useState<FlakeCoordinates[]>([
    {
      id: 1,
      topRight: { x: "", y: "" },
      bottomLeft: { x: "", y: "" }
    }
  ]);
  const [jsonOutput, setJsonOutput] = useState<string>("");
  const positionUpdateTargetRef = useRef<PositionUpdateTarget | null>(null);
  const [traceOverStatus, setTraceOverStatus] = useState<TraceOverResult | null>(null);
  const [magnification, setMagnification] = useState<number>(20); // Default magnification value
  const [picsUntilFocus, setPicsUntilFocus] = useState<number>(300); // Default pics until focus value
  const [initialWaitTime, setInitialWaitTime] = useState<number>(8); // Default initial wait time
  const [focusWaitTime, setFocusWaitTime] = useState<number>(8); // Default focus wait time
  const [cameraIndex, setCameraIndex] = useState<number>(0); // Default camera index
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });

  // Update flake coordinates when count changes
  useEffect(() => {
    if (flakeCount > flakeCoordinates.length) {
      // Add new flakes
      const newFlakes = Array.from({ length: flakeCount - flakeCoordinates.length }, (_, index) => ({
        id: flakeCoordinates.length + index + 1,
        topRight: { x: "", y: "" },
        bottomLeft: { x: "", y: "" }
      }));
      setFlakeCoordinates([...flakeCoordinates, ...newFlakes]);
    } else if (flakeCount < flakeCoordinates.length) {
      // Remove excess flakes
      setFlakeCoordinates(flakeCoordinates.slice(0, flakeCount));
    }
  }, [flakeCount]);

  // Update JSON output whenever flake coordinates change or parameters change
  useEffect(() => {
    // Convert flake coordinates to single boundary coordinates
    const flakesArray = flakeCoordinates.map(flake => ({
      id: flake.id,
      topRight: {
        x: flake.topRight.x ? parseFloat(flake.topRight.x) : null,
        y: flake.topRight.y ? parseFloat(flake.topRight.y) : null
      },
      bottomLeft: {
        x: flake.bottomLeft.x ? parseFloat(flake.bottomLeft.x) : null,
        y: flake.bottomLeft.y ? parseFloat(flake.bottomLeft.y) : null
      }
    }));

    // If we have at least one flake with valid coordinates, use it for the boundary
    const validFlake = flakesArray.find(flake => 
      flake.topRight.x !== null && flake.topRight.y !== null && 
      flake.bottomLeft.x !== null && flake.bottomLeft.y !== null
    );

    const output: any = {
      type: "TRACE_OVER",
      flakes: flakesArray,
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex
    };

    setJsonOutput(JSON.stringify(output, null, 2));
  }, [flakeCoordinates, magnification, picsUntilFocus, initialWaitTime, focusWaitTime, cameraIndex]);

  // Listen for position responses and trace over results from the server
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
    
    // Handle trace over results
    if (message.type === "TRACE_OVER_RESULT") {
      console.log("Received trace over result:", message);
      
      setTraceOverStatus({
        success: message.success,
        message: message.message || (message.success ? "Trace over completed successfully" : "Trace over failed"),
        flakeCount: message.flakeCount
      });
      
      // Clear status after 5 seconds
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 5000);
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

  const handleTraceOver = () => {
    // Validate that all coordinates are filled
    const isValid = flakeCoordinates.every(flake => 
      flake.topRight.x && flake.topRight.y && flake.bottomLeft.x && flake.bottomLeft.y
    );

    if (!isValid) {
      alert("Please fill in all coordinate fields before sending.");
      return;
    }

    // Send the trace over command with flake coordinates and all parameters
    const data = {
      type: "TRACE_OVER",
      flakes: flakeCoordinates.map(flake => ({
        id: flake.id,
        topRight: {
          x: parseFloat(flake.topRight.x),
          y: parseFloat(flake.topRight.y)
        },
        bottomLeft: {
          x: parseFloat(flake.bottomLeft.x),
          y: parseFloat(flake.bottomLeft.y)
        }
      })),
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex
    };

    sendJson(data);
  };

  const handleCoordinateChange = (
    flakeId: number, 
    corner: "topRight" | "bottomLeft", 
    axis: "x" | "y", 
    value: string
  ) => {
    // Only allow numbers and decimal points
    if (value !== "" && !/^-?\d*\.?\d*$/.test(value)) {
      return;
    }

    setFlakeCoordinates(prev => 
      prev.map(flake => 
        flake.id === flakeId 
          ? { 
              ...flake, 
              [corner]: { 
                ...flake[corner], 
                [axis]: value 
              } 
            } 
          : flake
      )
    );
  };

  const copyCurrentPosition = (
    flakeId: number, 
    corner: "topRight" | "bottomLeft" | "both"
  ) => {
    // Format the current position values
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);
    
    // Update the specific coordinate(s) with the current position
    if (corner === "both") {
      // Update both corners with the current position
      setFlakeCoordinates(prev => 
        prev.map(flake => 
          flake.id === flakeId 
            ? { 
                ...flake, 
                topRight: { 
                  x: xValue, 
                  y: yValue 
                },
                bottomLeft: {
                  x: xValue,
                  y: yValue
                }
              } 
            : flake
        )
      );
    } else {
      // Update the specific corner
      setFlakeCoordinates(prev => 
        prev.map(flake => 
          flake.id === flakeId 
            ? { 
                ...flake, 
                [corner]: { 
                  x: xValue, 
                  y: yValue 
                }
              } 
            : flake
        )
      );
    }
  };

  // Clear coordinates for a specific flake
  const clearFlakeCoordinates = (flakeId: number) => {
    setFlakeCoordinates(prev => 
      prev.map(flake => 
        flake.id === flakeId 
          ? { 
              ...flake, 
              topRight: { x: "", y: "" },
              bottomLeft: { x: "", y: "" }
            } 
          : flake
      )
    );
  };

  // Save JSON data to a file
  const saveJsonToFile = async () => {
    try {
      // Generate a filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const suggestedName = `trace-over-config-${timestamp}.json`;
      
      // Check if the File System Access API is supported
      if ('showSaveFilePicker' in window) {
        try {
          // Use the File System Access API to get a file handle
          const fileHandle = await (window as any).showSaveFilePicker({
            suggestedName,
            types: [{
              description: 'JSON Files',
              accept: { 'application/json': ['.json'] }
            }]
          });
          
          // Create a writable stream
          const writable = await fileHandle.createWritable();
          
          // Write the JSON data to the file
          await writable.write(jsonOutput);
          
          // Close the file
          await writable.close();
          
          // Show success message
          setTraceOverStatus({
            success: true,
            message: "JSON configuration saved successfully"
          });
        } catch (err: any) {
          // User cancelled the save dialog or other error
          if (err.name !== 'AbortError') {
            throw err;
          }
          return;
        }
      } else {
        // Fallback for browsers that don't support the File System Access API
        // Create a blob with the JSON data
        const blob = new Blob([jsonOutput], { type: 'application/json' });
        
        // Create a URL for the blob
        const url = URL.createObjectURL(blob);
        
        // Create a temporary anchor element
        const a = document.createElement('a');
        a.href = url;
        a.download = suggestedName;
        
        // Append to the document, click, and remove
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Release the URL object
        URL.revokeObjectURL(url);
        
        // Show success message with note about browser limitations
        setTraceOverStatus({
          success: true,
          message: "JSON configuration downloaded. Note: Your browser doesn't support choosing a save location."
        });
      }
      
      // Clear status after 5 seconds
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 5000);
    } catch (error: any) {
      console.error("Error saving JSON file:", error);
      
      // Show error message
      setTraceOverStatus({
        success: false,
        message: `Error saving JSON file: ${error.message || error}`
      });
    }
  };

  // Trigger file input click
  const handleImportClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle file selection
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        
        // Set the JSON output without parsing
        setJsonOutput(content);
        
        // Show success message
        setTraceOverStatus({
          success: true,
          message: "JSON file loaded. Click 'Parse JSON' to update the form."
        });
        
        // Clear status after 3 seconds
        setTimeout(() => {
          setTraceOverStatus(null);
        }, 3000);
      } catch (error) {
        console.error("Error reading JSON file:", error);
        setTraceOverStatus({
          success: false,
          message: "Error importing JSON file. Make sure it's a valid JSON file."
        });
      }
    };
    
    reader.onerror = () => {
      setTraceOverStatus({
        success: false,
        message: "Error reading the file"
      });
    };
    
    reader.readAsText(file);
    
    // Reset the file input so the same file can be selected again
    event.target.value = '';
  };

  // Update form fields from JSON
  const updateFormFromJson = (jsonString: string) => {
    try {
      const parsedJson = JSON.parse(jsonString);
      
      // Validate the JSON structure
      if (parsedJson.type !== "TRACE_OVER") {
        throw new Error("Invalid JSON: not a TRACE_OVER command");
      }
      
      if (parsedJson.flakes && Array.isArray(parsedJson.flakes)) {
        const newFlakes = parsedJson.flakes.map((flake: any) => ({
          id: flake.id || 1,
          topRight: {
            x: flake.topRight.x !== null ? String(flake.topRight.x) : "",
            y: flake.topRight.y !== null ? String(flake.topRight.y) : ""
          },
          bottomLeft: {
            x: flake.bottomLeft.x !== null ? String(flake.bottomLeft.x) : "",
            y: flake.bottomLeft.y !== null ? String(flake.bottomLeft.y) : ""
          }
        }));
        
        setFlakeCount(newFlakes.length);
        setFlakeCoordinates(newFlakes);
      }
      
      // Update other parameters if they exist
      if (typeof parsedJson.magnification === 'number') {
        setMagnification(parsedJson.magnification);
      }
      
      if (typeof parsedJson.pics_until_focus === 'number') {
        setPicsUntilFocus(parsedJson.pics_until_focus);
      }
      
      if (typeof parsedJson.initial_wait_time === 'number') {
        setInitialWaitTime(parsedJson.initial_wait_time);
      }
      
      if (typeof parsedJson.focus_wait_time === 'number') {
        setFocusWaitTime(parsedJson.focus_wait_time);
      }
      
      if (typeof parsedJson.camera_index === 'number') {
        setCameraIndex(parsedJson.camera_index);
      }
      
    } catch (error) {
      alert(`Error parsing JSON: ${(error as Error).message}`);
    }
  };

  // Handle manual edits to the JSON output
  const handleJsonOutputChange = (value: string) => {
    // Just update the text without trying to parse
    setJsonOutput(value);
  };

  // Handle tab key in the JSON textarea
  const handleJsonKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      
      // Insert tab at cursor position (2 spaces)
      const newValue = jsonOutput.substring(0, start) + '  ' + jsonOutput.substring(end);
      setJsonOutput(newValue);
      
      // Move cursor after the inserted tab
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 2;
        target.focus();
      }, 0);
    }
  };

  // Parse the JSON and update form fields when Parse button is clicked
  const handleParseJson = () => {
    try {
      updateFormFromJson(jsonOutput);
      
      // Show success message
      setTraceOverStatus({
        success: true,
        message: "JSON parsed and form updated successfully"
      });
      
      // Clear status after 3 seconds
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 3000);
    } catch (error) {
      console.error("Error parsing JSON:", error);
      setTraceOverStatus({
        success: false,
        message: "Error parsing JSON. Make sure it's a valid trace over configuration."
      });
    }
  };

  // Get status message color based on success/failure
  const getStatusColor = () => {
    if (!traceOverStatus) return "";
    return traceOverStatus.success ? "text-green-600" : "text-red-600";
  };

  // Add this function before the return statement
  const switchCoordinates = (flakeId: number) => {
    setFlakeCoordinates(prev => 
      prev.map(flake => 
        flake.id === flakeId 
          ? { 
              ...flake, 
              topRight: { ...flake.bottomLeft },
              bottomLeft: { ...flake.topRight }
            } 
          : flake
      )
    );
  };

  // Handle cancellation of the trace over execution
  const handleCancelExecution = () => {
    sendJson({
      type: "CANCEL_EXECUTION"
    });
        
    // Clear status after 3 seconds
    setTimeout(() => {
      setTraceOverStatus(null);
    }, 3000);
  };

  return (
    <div className="trace-over-box">
      <h2>Trace Over</h2>
      <div className="trace-container">
        <div className="flex justify-between items-center mb-4">
          {/* Removed Number of Flakes control from here */}
        </div>

        {/* Trace Settings Controls */}
        <div className="trace-settings flex flex-wrap gap-3 mb-4 bg-gray-50 p-3 rounded border">
          <h3 className="w-full text-sm font-medium mb-2 text-gray-700">Trace Settings:</h3>
          
          <div className="setting-control flex items-center">
            <label className="text-sm font-medium mr-2">
              Magnification:
            </label>
            <select
              value={magnification}
              onChange={(e) => setMagnification(parseInt(e.target.value))}
              className="p-1 border rounded w-16 text-center"
            >
              <option value="5">5x</option>
              <option value="10">10x</option>
              <option value="20">20x</option>
              <option value="40">40x</option>
              <option value="50">50x</option>
              <option value="100">100x</option>
            </select>
          </div>
          
          <div className="setting-control flex items-center">
            <label className="text-sm font-medium mr-2">
              Pics Until Focus:
            </label>
            <input
              type="number"
              min="1"
              value={picsUntilFocus}
              onChange={(e) => setPicsUntilFocus(Math.max(1, parseInt(e.target.value) || 300))}
              className="p-1 border rounded w-16 text-center"
            />
          </div>
          
          <div className="setting-control flex items-center">
            <label className="text-sm font-medium mr-2">
              Initial Wait (s):
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={initialWaitTime}
              onChange={(e) => setInitialWaitTime(Math.max(0, parseFloat(e.target.value) || 8))}
              className="p-1 border rounded w-16 text-center"
            />
          </div>
          
          <div className="setting-control flex items-center">
            <label className="text-sm font-medium mr-2">
              Focus Wait (s):
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={focusWaitTime}
              onChange={(e) => setFocusWaitTime(Math.max(0, parseFloat(e.target.value) || 8))}
              className="p-1 border rounded w-16 text-center"
            />
          </div>
          
          <div className="setting-control flex items-center">
            <label className="text-sm font-medium mr-2">
              Camera Index:
            </label>
            <input
              type="number"
              min="0"
              value={cameraIndex}
              onChange={(e) => setCameraIndex(Math.max(0, parseInt(e.target.value) || 0))}
              className="p-1 border rounded w-16 text-center"
            />
          </div>
        </div>
        
        {/* Add Number of Flakes control below Trace Settings */}
        <div className="number-of-flakes-control mb-4 flex items-center">
          <label className="text-sm font-medium">
            Number of Flakes:
            <input
              type="number"
              min="1"
              value={flakeCount}
              onChange={(e) => setFlakeCount(Math.max(1, parseInt(e.target.value) || 1))}
              className="ml-2 p-1 border rounded w-16 text-center"
            />
          </label>
        </div>

        {/* Current Position Display
        <div className="current-position mb-2 text-xs text-gray-600">
          Current Position: X: {currentPosition.x.toFixed(3)}, Y: {currentPosition.y.toFixed(3)}
        </div> */}

        {/* Compact Flake Coordinates Table */}
        <div className="flake-coordinates-container overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-1 text-left">Flake</th>
                <th className="p-1 text-left">Top Right X</th>
                <th className="p-1 text-left">Top Right Y</th>
                <th className="p-1 text-left">Bottom Left X</th>
                <th className="p-1 text-left">Bottom Left Y</th>
                <th className="p-1 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {flakeCoordinates.map((flake) => (
                <tr key={flake.id} className="border-b">
                  <td className="p-1 font-medium">{flake.id}</td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={flake.topRight.x}
                      onChange={(e) => handleCoordinateChange(flake.id, "topRight", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={flake.topRight.y}
                      onChange={(e) => handleCoordinateChange(flake.id, "topRight", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={flake.bottomLeft.x}
                      onChange={(e) => handleCoordinateChange(flake.id, "bottomLeft", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={flake.bottomLeft.y}
                      onChange={(e) => handleCoordinateChange(flake.id, "bottomLeft", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <div className="flex space-x-1">
                      <button
                        onClick={() => copyCurrentPosition(flake.id, "topRight")}
                        className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
                        title="Copy current position to Top Right"
                      >
                        TR
                      </button>
                      <button
                        onClick={() => copyCurrentPosition(flake.id, "bottomLeft")}
                        className="px-2 py-1 bg-green-500 text-white text-xs rounded"
                        title="Copy current position to Bottom Left"
                      >
                        BL
                      </button>
                      <button
                        onClick={() => switchCoordinates(flake.id)}
                        className="px-2 py-1 bg-purple-500 text-white text-xs rounded"
                        title="Switch top right and bottom left coordinates"
                      >
                        Switch
                      </button>
                      <button
                        onClick={() => clearFlakeCoordinates(flake.id)}
                        className="px-2 py-1 bg-red-500 text-white text-xs rounded"
                        title="Clear coordinates"
                      >
                        Clear
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* JSON Output */}
        <div className="json-output-container mt-4">
          <div className="flex justify-between items-center mb-1">
            <h3 className="text-sm font-medium">JSON Output:</h3>
            <div className="flex space-x-2">
              <button
                onClick={handleImportClick}
                className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
                title="Import JSON from file"
              >
                Import JSON
              </button>
              <button
                onClick={handleParseJson}
                className="px-3 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700"
                title="Parse JSON and update form fields"
              >
                Parse JSON
              </button>
              <button
                onClick={saveJsonToFile}
                className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                title="Save JSON to file"
              >
                Save JSON
              </button>
              {/* Hidden file input for importing */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".json"
                className="hidden"
              />
            </div>
          </div>
          <textarea
            value={jsonOutput}
            onChange={(e) => handleJsonOutputChange(e.target.value)}
            onKeyDown={handleJsonKeyDown}
            className="ts-parameters-input-field w-full h-32 p-2 border rounded font-mono text-xs"
            spellCheck="false"
            wrap="off"
          />
        </div>

        {/* Status Message */}
        {traceOverStatus && (
          <div className={`status-message mt-2 text-sm ${getStatusColor()}`}>
            {traceOverStatus.message}
            {traceOverStatus.flakeCount !== undefined && (
              <span> ({traceOverStatus.flakeCount} flakes processed)</span>
            )}
          </div>
        )}

        <div className="trace-actions mt-4 flex space-x-2">
          <button 
            className="trace-button px-4 py-2 rounded text-white bg-green-600 hover:bg-green-700"
            onClick={handleTraceOver}
          >
            Send Trace Over Command
          </button>
          <button 
            className="trace-button px-4 py-2 rounded text-white bg-red-600 hover:bg-red-700"
            onClick={handleCancelExecution}
          >
            Cancel Execution
          </button>
        </div>
      </div>
    </div>
  );
};

export default TraceOverBox; 