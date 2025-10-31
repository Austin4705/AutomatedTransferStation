import { useSendJSON } from "../../hooks/useSendJSON";
import { useState, useEffect, useRef, ChangeEvent } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { positionSettingsAtom } from "../../state/appState";

interface WaferCoordinates {
  key: string; // Stable key for React rendering
  id: string;  // User-editable wafer ID
  start: { x: string; y: string };
  end: { x: string; y: string };
}

interface Position {
  x: number;
  y: number;
  [key: string]: number;
}

interface PositionUpdateTarget {
  waferId: string;
  corner: "start" | "end" | "both";
}

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
      key: "wafer-0",
      id: "1",
      start: { x: "", y: "" },
      end: { x: "", y: "" }
    }
  ]);
  const [jsonOutput, setJsonOutput] = useState<string>("");
  const positionUpdateTargetRef = useRef<PositionUpdateTarget | null>(null);
  const [traceOverStatus, setTraceOverStatus] = useState<TraceOverResult | null>(null);
  const [magnification, setMagnification] = useState<number>(20);
  const [picsUntilFocus, setPicsUntilFocus] = useState<number>(300);
  const [initialWaitTime, setInitialWaitTime] = useState<number>(8);
  const [focusWaitTime, setFocusWaitTime] = useState<number>(8);
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [saveImages, setSaveImages] = useState<boolean>(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });
  const positionSettings = useRecoilValue(positionSettingsAtom);
  const position = positionSettings.currentPosition;

  useEffect(() => {
    if (waferCount > waferCoordinates.length) {
      const newWafers = Array.from({ length: waferCount - waferCoordinates.length }, (_, index) => {
        const waferIndex = waferCoordinates.length + index;
        return {
          key: `wafer-${waferIndex}`,
          id: String(waferIndex + 1),
          start: { x: "", y: "" },
          end: { x: "", y: "" }
        };
      });
      setWaferCoordinates([...waferCoordinates, ...newWafers]);
    } else if (waferCount < waferCoordinates.length) {
      setWaferCoordinates(waferCoordinates.slice(0, waferCount));
    }
  }, [waferCount]);

  useEffect(() => {
    const wafersArray = waferCoordinates.map(wafer => ({
      id: wafer.id,
      start: {
        x: wafer.start.x ? parseFloat(wafer.start.x) : "",
        y: wafer.start.y ? parseFloat(wafer.start.y) : ""
      },
      end: {
        x: wafer.end.x ? parseFloat(wafer.end.x) : "",
        y: wafer.end.y ? parseFloat(wafer.end.y) : ""
      }
    }));

    const validWafer = wafersArray.find(wafer =>
      wafer.start.x !== "" && wafer.start.y !== "" &&
      wafer.end.x !== "" && wafer.end.y !== ""
    );

    const traceOverConfig = {
      wafers: wafersArray,
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex,
      save_images: saveImages
    };

    const output: any = {
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "RUN_TRACE_OVER",
      parameters: [traceOverConfig]
    };

    setJsonOutput(JSON.stringify(output, null, 2));
  }, [waferCoordinates, magnification, picsUntilFocus, initialWaitTime, focusWaitTime, cameraIndex, saveImages]);

  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;
    
    if (message.type === "POSITION" || message.type === "RESPONSE_POSITION") {
      if (typeof message.x === 'number' && typeof message.y === 'number') {
        setCurrentPosition({
          x: message.x,
          y: message.y
        });
      }
    }
    
    if (message.type === "TRACE_OVER_RESULT") {
      console.log("Received trace over result:", message);
      
      setTraceOverStatus({
        success: message.success,
        message: message.message || (message.success ? "Trace over completed successfully" : "Trace over failed"),
        waferCount: message.waferCount
      });
      
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 5000);
    }
  }, [jsonState.lastJsonMessage]);

  useEffect(() => {
    if (position) {
      setCurrentPosition({
        x: position.x,
        y: position.y
      });
    }
  }, [position]);

  const handleTraceOver = () => {
    const isValid = waferCoordinates.every(wafer =>
      wafer.start.x && wafer.start.y && wafer.end.x && wafer.end.y
    );

    if (!isValid) {
      alert("Please fill in all coordinate fields before sending.");
      return;
    }

    const traceOverConfig = {
      wafers: waferCoordinates.map(wafer => ({
        id: wafer.id,
        start: {
          x: parseFloat(wafer.start.x),
          y: parseFloat(wafer.start.y)
        },
        end: {
          x: parseFloat(wafer.end.x),
          y: parseFloat(wafer.end.y)
        }
      })),
      magnification: magnification,
      pics_until_focus: picsUntilFocus,
      initial_wait_time: initialWaitTime,
      focus_wait_time: focusWaitTime,
      camera_index: cameraIndex,
      save_images: saveImages
    };

    const data = {
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "RUN_TRACE_OVER",
      parameters: JSON.stringify([traceOverConfig])
    };

    sendJson(data);
  };

  const handleCoordinateChange = (
    waferId: string,
    corner: "start" | "end",
    axis: "x" | "y",
    value: string
  ) => {
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

  const handleWaferIdChange = (waferKey: string, newId: string) => {
    setWaferCoordinates(prev =>
      prev.map(wafer =>
        wafer.key === waferKey
          ? { ...wafer, id: newId }
          : wafer
      )
    );
  };

  const copyCurrentPosition = (
    waferId: string,
    corner: "start" | "end" | "both"
  ) => {
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);

    if (corner === "both") {
      setWaferCoordinates(prev =>
        prev.map(wafer =>
          wafer.id === waferId
            ? {
                ...wafer,
                start: {
                  x: xValue,
                  y: yValue
                },
                end: {
                  x: xValue,
                  y: yValue
                }
              }
            : wafer
        )
      );
    } else {
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

  const clearWaferCoordinates = (waferId: string) => {
    setWaferCoordinates(prev =>
      prev.map(wafer =>
        wafer.id === waferId
          ? {
              ...wafer,
              start: { x: "", y: "" },
              end: { x: "", y: "" }
            }
          : wafer
      )
    );
  };

  const saveJsonToFile = async () => {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const suggestedName = `trace-over-config-${timestamp}.json`;
      
      if ('showSaveFilePicker' in window) {
        try {
          const fileHandle = await (window as any).showSaveFilePicker({
            suggestedName,
            types: [{
              description: 'JSON Files',
              accept: { 'application/json': ['.json'] }
            }]
          });
          
          const writable = await fileHandle.createWritable();
          
          await writable.write(jsonOutput);
          
          await writable.close();
          
          setTraceOverStatus({
            success: true,
            message: "JSON configuration saved successfully"
          });
        } catch (err: any) {
          if (err.name !== 'AbortError') {
            throw err;
          }
          return;
        }
      } else {
        const blob = new Blob([jsonOutput], { type: 'application/json' });
        
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = suggestedName;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        setTraceOverStatus({
          success: true,
          message: "JSON configuration downloaded. Note: Your browser doesn't support choosing a save location."
        });
      }
      
      setTimeout(() => {
        setTraceOverStatus(null);
      }, 5000);
    } catch (error: any) {
      console.error("Error saving JSON file:", error);
      
      setTraceOverStatus({
        success: false,
        message: `Error saving JSON file: ${error.message || error}`
      });
    }
  };

  const handleImportClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        
        setJsonOutput(content);
        
        setTraceOverStatus({
          success: true,
          message: "JSON file loaded. Click 'Parse JSON' to update the form."
        });
        
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
    
    event.target.value = '';
  };

  const updateFormFromJson = (jsonString: string) => {
    try {
      const parsedJson = JSON.parse(jsonString);

      if (parsedJson.type !== "EXECUTE_TRANSFER_FUNCTION") {
        throw new Error("Invalid JSON: must be an EXECUTE_TRANSFER_FUNCTION command");
      }

      if (!parsedJson.parameters) {
        throw new Error("Invalid JSON: missing parameters field");
      }

      // Extract from parameters
      const params = typeof parsedJson.parameters === 'string'
        ? JSON.parse(parsedJson.parameters)
        : parsedJson.parameters;

      const settings = params[0];
      if (!settings) {
        throw new Error("Invalid JSON: parameters array is empty");
      }

      const wafers = settings.wafers;

      if (wafers && Array.isArray(wafers)) {
        const newWafers = wafers.map((wafer: any, index: number) => ({
          key: `wafer-${index}`,  // Add stable key for React rendering
          id: wafer.id?.toString() || String(index + 1),  // Preserve string/number ID from JSON
          start: {
            x: wafer.start?.x?.toString() || "",
            y: wafer.start?.y?.toString() || ""
          },
          end: {
            x: wafer.end?.x?.toString() || "",
            y: wafer.end?.y?.toString() || ""
          }
        }));

        setWaferCount(newWafers.length);
        setWaferCoordinates(newWafers);
      }

      if (typeof settings.magnification === 'number') {
        setMagnification(settings.magnification);
      }

      if (typeof settings.pics_until_focus === 'number') {
        setPicsUntilFocus(settings.pics_until_focus);
      }

      if (typeof settings.initial_wait_time === 'number') {
        setInitialWaitTime(settings.initial_wait_time);
      }

      if (typeof settings.focus_wait_time === 'number') {
        setFocusWaitTime(settings.focus_wait_time);
      }

      if (typeof settings.camera_index === 'number') {
        setCameraIndex(settings.camera_index);
      }

      if (typeof settings.save_images === 'boolean') {
        setSaveImages(settings.save_images);
      }
      
    } catch (error) {
      console.error("Error parsing JSON:", error);
      alert("Invalid JSON format. Please check your input.");
    }
  };

  const handleJsonOutputChange = (value: string) => {
    setJsonOutput(value);
  };

  const handleJsonKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      
      const newValue = jsonOutput.substring(0, start) + '  ' + jsonOutput.substring(end);
      setJsonOutput(newValue);
      
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 2;
        target.focus();
      }, 0);
    }
  };

  const handleParseJson = () => {
    try {
      updateFormFromJson(jsonOutput);
      
      setTraceOverStatus({
        success: true,
        message: "JSON parsed and form updated successfully"
      });
      
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

  const getStatusColor = () => {
    if (!traceOverStatus) return "";
    return traceOverStatus.success ? "text-green-600" : "text-red-600";
  };

  const switchCoordinates = (waferId: string) => {
    setWaferCoordinates(prev =>
      prev.map(wafer =>
        wafer.id === waferId
          ? {
              ...wafer,
              start: { ...wafer.end },
              end: { ...wafer.start }
            }
          : wafer
      )
    );
  };

  const handleCancelExecution = () => {
    sendJson({
      type: "CANCEL_EXECUTION"
    });
        
    setTimeout(() => {
      setTraceOverStatus(null);
    }, 3000);
  };

  const handleEnableTraceOverExecution = () => {
    sendJson({
      type: "EXECUTE_TRACE_OVER",
      state: true
    });
    
    setTraceOverStatus({
      success: true,
      message: "Trace over execution enabled"
    });
    
    setTimeout(() => {
      setTraceOverStatus(null);
    }, 3000);
  };

  const handleDisableTraceOverExecution = () => {
    sendJson({
      type: "EXECUTE_TRACE_OVER",
      state: false
    });
    
    setTraceOverStatus({
      success: true,
      message: "Trace over execution paused"
    });
    
    setTimeout(() => {
      setTraceOverStatus(null);
    }, 3000);
  };

  return (
    <div className="trace-over-box">
      <h2>Trace Over</h2>
      <div className="trace-container">
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

        <div className="current-position mb-2 text-xs text-gray-600">
          Current Position: X: {currentPosition.x.toFixed(3)}, Y: {currentPosition.y.toFixed(3)}
        </div>

        <div className="wafer-coordinates-container overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-1 text-left">Wafer</th>
                <th className="p-1 text-left">Start X</th>
                <th className="p-1 text-left">Start Y</th>
                <th className="p-1 text-left">End X</th>
                <th className="p-1 text-left">End Y</th>
                <th className="p-1 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {waferCoordinates.map((wafer) => (
                <tr key={wafer.key} className="border-b">
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.id}
                      onChange={(e) => handleWaferIdChange(wafer.key, e.target.value)}
                      className="p-1 border rounded w-16 text-xs font-medium"
                      placeholder="ID"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.start.x}
                      onChange={(e) => handleCoordinateChange(wafer.id, "start", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.start.y}
                      onChange={(e) => handleCoordinateChange(wafer.id, "start", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.end.x}
                      onChange={(e) => handleCoordinateChange(wafer.id, "end", "x", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="X"
                    />
                  </td>
                  <td className="p-1">
                    <input
                      type="text"
                      value={wafer.end.y}
                      onChange={(e) => handleCoordinateChange(wafer.id, "end", "y", e.target.value)}
                      className="p-1 border rounded w-20 text-xs"
                      placeholder="Y"
                    />
                  </td>
                  <td className="p-1">
                    <div className="flex space-x-1">
                      <button
                        onClick={() => copyCurrentPosition(wafer.id, "start")}
                        className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
                        title="Copy current position to Start"
                      >
                        Start
                      </button>
                      <button
                        onClick={() => copyCurrentPosition(wafer.id, "end")}
                        className="px-2 py-1 bg-green-500 text-white text-xs rounded"
                        title="Copy current position to End"
                      >
                        End
                      </button>
                      <button
                        onClick={() => switchCoordinates(wafer.id)}
                        className="px-2 py-1 bg-purple-500 text-white text-xs rounded"
                        title="Switch start and end coordinates"
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