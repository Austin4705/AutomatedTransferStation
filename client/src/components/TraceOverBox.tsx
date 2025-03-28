import { useSendJSON } from "../hooks/useSendJSON";
import { useState, useEffect, useRef, ChangeEvent } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { usePositionContext } from "../state/positionContext";

// Interface for flake coordinates
interface WaferCoordinates {
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
  waferId: number;
  corner: "topRight" | "bottomLeft" | "both";
}

// Interface for trace over result
interface TraceOverResult {
  success: boolean;
  message: string;
  waferCount?: number;
}

const TraceOverBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const [waferCount, setWaferCount] = useState<number>(1);
  const [waferCoordinates, setWaferCoordinates] = useState<WaferCoordinates[]>([
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
  const [saveImages, setSaveImages] = useState<boolean>(true); // Default save images value
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });
  const { autoUpdate, pollRate, position } = usePositionContext();

  // Update wafer coordinates when count changes
  useEffect(() => {
    if (waferCount > waferCoordinates.length) {
      // Add new wafers
      const newWafers = Array.from({ length: waferCount - waferCoordinates.length }, (_, index) => ({
        id: waferCoordinates.length + index + 1,
        topRight: { x: "", y: "" },
        bottomLeft: { x: "", y: "" }
      }));
      setWaferCoordinates([...waferCoordinates, ...newWafers]);
    } else if (waferCount < waferCoordinates.length) {
      // Remove excess wafers
      setWaferCoordinates(waferCoordinates.slice(0, waferCount));
    }
  }, [waferCount]);

  // Update JSON output whenever wafer coordinates change or parameters change
  useEffect(() => {
    // Convert wafer coordinates to single boundary coordinates
    const wafersArray = waferCoordinates.map(wafer => ({
      id: wafer.id,
      topRight: {
        x: wafer.topRight.x ? parseFloat(wafer.topRight.x) : null,
        y: wafer.topRight.y ? parseFloat(wafer.topRight.y) : null
      },
      bottomLeft: {
        x: wafer.bottomLeft.x ? parseFloat(wafer.bottomLeft.x) : null,
        y: wafer.bottomLeft.y ? parseFloat(wafer.bottomLeft.y) : null
      }
    }));

    // If we have at least one wafer with valid coordinates, use it for the boundary
    const validWafer = wafersArray.find(wafer => 
      wafer.topRight.x !== null && wafer.topRight.y !== null && 
      wafer.bottomLeft.x !== null && wafer.bottomLeft.y !== null
    );

    const output: any = {
      type: "TRACE_OVER",
      wafers: wafersArray,
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex,
      save_images: saveImages
    };

    setJsonOutput(JSON.stringify(output, null, 2));
  }, [waferCoordinates, magnification, picsUntilFocus, initialWaitTime, focusWaitTime, cameraIndex, saveImages]);

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
        waferCount: message.waferCount
      });
      
      // Clear status after 5 seconds
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 5000);
    }
  }, [jsonState.lastJsonMessage]);

  // Initialize position polling based on autoUpdate setting
  useEffect(() => {
    // NO NEED TO IMPLEMENT CUSTOM POLLING HERE
    // Position will be updated automatically through the context
    
    // We can listen for position changes through the context
    // and update the current position state
    if (position) {
      setCurrentPosition({
        x: position.x,
        y: position.y
      });
    }
  }, [position]);

  const handleTraceOver = () => {
    // Validate that all coordinates are filled
    const isValid = waferCoordinates.every(wafer => 
      wafer.topRight.x && wafer.topRight.y && wafer.bottomLeft.x && wafer.bottomLeft.y
    );

    if (!isValid) {
      alert("Please fill in all coordinate fields before sending.");
      return;
    }

    // Send the trace over command with wafer coordinates and all parameters
    const data = {
      type: "TRACE_OVER",
      wafers: waferCoordinates.map(wafer => ({
        id: wafer.id,
        topRight: {
          x: parseFloat(wafer.topRight.x),
          y: parseFloat(wafer.topRight.y)
        },
        bottomLeft: {
          x: parseFloat(wafer.bottomLeft.x),
          y: parseFloat(wafer.bottomLeft.y)
        }
      })),
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex,
      save_images: saveImages
    };

    sendJson(data);
  };

  const handleCoordinateChange = (
    waferId: number, 
    corner: "topRight" | "bottomLeft", 
    axis: "x" | "y", 
    value: string
  ) => {
    // Only allow numbers and decimal points
    if (value !== "" && !/^-?\d*\.?\d*$/.test(value)) {
      return;
    }

    setWaferCoordinates(prev => 
      prev.map(wafer => 
        wafer.id === waferId 
          ? { 
              ...wafer, 
              [corner]: { 
                ...wafer[corner], 
                [axis]: value 
              } 
            } 
          : wafer
      )
    );
  };

  const copyCurrentPosition = (
    waferId: number, 
    corner: "topRight" | "bottomLeft" | "both"
  ) => {
    // Format the current position values
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);
    
    // Update the specific coordinate(s) with the current position
    if (corner === "both") {
      // Update both corners with the current position
      setWaferCoordinates(prev => 
        prev.map(wafer => 
          wafer.id === waferId 
            ? { 
                ...wafer, 
                topRight: { 
                  x: xValue, 
                  y: yValue 
                },
                bottomLeft: {
                  x: xValue,
                  y: yValue
                }
              } 
            : wafer
        )
      );
    } else {
      // Update the specific corner
      setWaferCoordinates(prev => 
        prev.map(wafer => 
          wafer.id === waferId 
            ? { 
                ...wafer, 
                [corner]: { 
                  x: xValue, 
                  y: yValue 
                }
              } 
            : wafer
        )
      );
    }
  };

  // Clear coordinates for a specific wafer
  const clearWaferCoordinates = (waferId: number) => {
    setWaferCoordinates(prev => 
      prev.map(wafer => 
        wafer.id === waferId 
          ? { 
              ...wafer, 
              topRight: { x: "", y: "" },
              bottomLeft: { x: "", y: "" }
            } 
          : wafer
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
      
      if (parsedJson.wafers && Array.isArray(parsedJson.wafers)) {
        const newWafers = parsedJson.wafers.map((wafer: any, index: number) => ({
          id: index + 1,
          topRight: {
            x: wafer.topRight?.x?.toString() || "",
            y: wafer.topRight?.y?.toString() || ""
          },
          bottomLeft: {
            x: wafer.bottomLeft?.x?.toString() || "",
            y: wafer.bottomLeft?.y?.toString() || ""
          }
        }));
        
        setWaferCount(newWafers.length);
        setWaferCoordinates(newWafers);
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
      
      if (typeof parsedJson.save_images === 'boolean') {
        setSaveImages(parsedJson.save_images);
      }
      
    } catch (error) {
      console.error("Error parsing JSON:", error);
      alert("Invalid JSON format. Please check your input.");
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
  const switchCoordinates = (waferId: number) => {
    setWaferCoordinates(prev => 
      prev.map(wafer => 
        wafer.id === waferId 
          ? { 
              ...wafer, 
              topRight: { ...wafer.bottomLeft },
              bottomLeft: { ...wafer.topRight }
            } 
          : wafer
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

  // Handle enabling trace over execution
  const handleEnableTraceOverExecution = () => {
    sendJson({
      type: "EXECUTE_TRACE_OVER",
      state: true
    });
    
    setTraceOverStatus({
      success: true,
      message: "Trace over execution enabled"
    });
    
    // Clear status after 3 seconds
    setTimeout(() => {
      setTraceOverStatus(null);
    }, 3000);
  };

  // Handle disabling trace over execution
  const handleDisableTraceOverExecution = () => {
    sendJson({
      type: "EXECUTE_TRACE_OVER",
      state: false
    });
    
    setTraceOverStatus({
      success: true,
      message: "Trace over execution paused"
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
          
          <div className="setting-control flex items-center">
            <input
              type="checkbox"
              id="save-images"
              checked={saveImages}
              onChange={(e) => setSaveImages(e.target.checked)}
              className="mr-1"
            />
            <label htmlFor="save-images" className="text-sm font-medium cursor-pointer">
              Save Images
            </label>
          </div>
        </div>
        
        {/* Add Number of Wafers control below Trace Settings */}
        <div className="number-of-wafers-control mb-4 flex items-center">
          <label className="text-sm font-medium">
            Number of Wafers:
            <input
              type="number"
              min="1"
              value={waferCount}
              onChange={(e) => setWaferCount(Math.max(1, parseInt(e.target.value) || 1))}
              className="ml-2 p-1 border rounded w-16 text-center"
            />
          </label>
        </div>

        {/* Current Position Display */}
        <div className="current-position mb-2 text-xs text-gray-600">
          Current Position: X: {currentPosition.x.toFixed(3)}, Y: {currentPosition.y.toFixed(3)}
        </div>

        {/* Compact Wafer Coordinates Table */}
        <div className="wafer-coordinates-container overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-1 text-left">Wafer</th>
                <th className="p-1 text-left">Top Right X</th>
                <th className="p-1 text-left">Top Right Y</th>
                <th className="p-1 text-left">Bottom Left X</th>
                <th className="p-1 text-left">Bottom Left Y</th>
                <th className="p-1 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {waferCoordinates.map((wafer) => (
                <tr key={wafer.id} className="border-b">
                  <td className="p-1 font-medium">{wafer.id}</td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.topRight.x}
                      onChange={(e) => handleCoordinateChange(wafer.id, "topRight", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.topRight.y}
                      onChange={(e) => handleCoordinateChange(wafer.id, "topRight", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.bottomLeft.x}
                      onChange={(e) => handleCoordinateChange(wafer.id, "bottomLeft", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.bottomLeft.y}
                      onChange={(e) => handleCoordinateChange(wafer.id, "bottomLeft", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <div className="flex space-x-1">
                      <button
                        onClick={() => copyCurrentPosition(wafer.id, "topRight")}
                        className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
                        title="Copy current position to Top Right"
                      >
                        TR
                      </button>
                      <button
                        onClick={() => copyCurrentPosition(wafer.id, "bottomLeft")}
                        className="px-2 py-1 bg-green-500 text-white text-xs rounded"
                        title="Copy current position to Bottom Left"
                      >
                        BL
                      </button>
                      <button
                        onClick={() => switchCoordinates(wafer.id)}
                        className="px-2 py-1 bg-purple-500 text-white text-xs rounded"
                        title="Switch top right and bottom left coordinates"
                      >
                        Switch
                      </button>
                      <button
                        onClick={() => clearWaferCoordinates(wafer.id)}
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
            {traceOverStatus.waferCount !== undefined && (
              <span> ({traceOverStatus.waferCount} wafers processed)</span>
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
          <button 
            className="trace-button px-4 py-2 rounded text-white bg-green-500 hover:bg-green-600"
            onClick={handleEnableTraceOverExecution}
          >
            Enable Trace Over Execution
          </button>
          <button 
            className="trace-button px-4 py-2 rounded text-white bg-orange-500 hover:bg-orange-600"
            onClick={handleDisableTraceOverExecution}
          >
            Disable Trace Over Execution
          </button>
        </div>
      </div>
    </div>
  );
};

export default TraceOverBox; 