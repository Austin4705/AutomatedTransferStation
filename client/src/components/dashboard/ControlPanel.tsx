import { useState } from "react";
import { useSendJSON } from "../../hooks/useSendJSON";
import { useRecoilValue } from "recoil";
import { positionSettingsAtom } from "../../state/appState";

const ControlPanel = () => {
  const sendJson = useSendJSON();
  const [distance, setDistance] = useState<number>(1);
  const [gotoX, setGotoX] = useState<string>("");
  const [gotoY, setGotoY] = useState<string>("");
  const [exposureTime, setExposureTime] = useState<number>(5);
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const positionSettings = useRecoilValue(positionSettingsAtom);
  const position = positionSettings.currentPosition;

  // Execution Control Handlers
  const handlePause = () => {
    sendJson({
      type: "PAUSE_EXECUTION"
    });
  };

  const handleResume = () => {
    sendJson({
      type: "RESUME_EXECUTION"
    });
  };

  const handleCancel = () => {
    sendJson({
      type: "CANCEL_EXECUTION"
    });
  };

  // Movement Handlers
  const handleMove = (axis: 'x' | 'y' | 'z', direction: number) => {
    const currentPos = {
      x: position?.x || 0,
      y: position?.y || 0,
      z: position?.z || 0
    };

    const delta = direction * distance;

    if (axis === 'x') {
      sendJson({
        type: "EXECUTE_TRANSFER_FUNCTION",
        transfer_function_name: "MOVEX",
        parameters: JSON.stringify([{ x: currentPos.x + delta }])
      });
    } else if (axis === 'y') {
      sendJson({
        type: "EXECUTE_TRANSFER_FUNCTION",
        transfer_function_name: "MOVEY",
        parameters: JSON.stringify([{ y: currentPos.y + delta }])
      });
    } else if (axis === 'z') {
      sendJson({
        type: "EXECUTE_TRANSFER_FUNCTION",
        transfer_function_name: "MOVEZ",
        parameters: JSON.stringify([{ z: currentPos.z + delta }])
      });
    }
  };

  const handleHome = () => {
    sendJson({
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "MOVEXY",
      parameters: JSON.stringify([{ x: 0, y: 0 }])
    });
  };

  const handleGotoXY = () => {
    const x = parseFloat(gotoX);
    const y = parseFloat(gotoY);

    if (isNaN(x) || isNaN(y)) {
      alert("Please enter valid X and Y coordinates");
      return;
    }

    sendJson({
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "MOVEXY",
      parameters: JSON.stringify([{ x: x, y: y }])
    });
  };

  const handleSetExposure = () => {
    // Convert ms to microseconds (us)
    const exposure_time_us = exposureTime * 1000;

    sendJson({
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "SET_EXPOSURE_TIME",
      parameters: JSON.stringify([{
        camera_index: cameraIndex,
        exposure_time_us: exposure_time_us
      }])
    });
  };

  return (
    <div className="control-panel flex flex-col gap-4">
      {/* Execution Controls */}
      <div className="execution-controls">
        <h3 className="text-sm font-medium mb-2">Execution Controls</h3>
        <div className="flex gap-2">
          <button
            onClick={handlePause}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm"
          >
            Pause
          </button>
          <button
            onClick={handleResume}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
          >
            Resume
          </button>
          <button
            onClick={handleCancel}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Movement Controls */}
      <div className="movement-controls">
        <h3 className="text-sm font-medium mb-2">Movement Controls</h3>

        {/* Distance Selector */}
        <div className="flex items-center gap-2 mb-3">
          <label className="text-sm font-medium">Distance per click:</label>
          <select
            value={distance}
            onChange={(e) => setDistance(parseFloat(e.target.value))}
            className="p-1 border rounded text-sm"
          >
            <option value="0.1">0.1</option>
            <option value="0.5">0.5</option>
            <option value="1">1</option>
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>

        <div className="flex gap-4">
          {/* XY Movement Pad */}
          <div className="xy-movement flex flex-col items-center">
            <div className="text-xs mb-1 font-medium">XY Movement</div>
            <div className="grid grid-cols-3 gap-1">
              {/* Top Row */}
              <div></div>
              <button
                onClick={() => handleMove('y', 1)}
                className="w-12 h-12 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center"
                title="Move Up (Y+)"
              >
                ↑
              </button>
              <div></div>

              {/* Middle Row */}
              <button
                onClick={() => handleMove('x', -1)}
                className="w-12 h-12 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center"
                title="Move Left (X-)"
              >
                ←
              </button>
              <button
                onClick={handleHome}
                className="w-12 h-12 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center justify-center text-xs"
                title="Home (0, 0)"
              >
                Home
              </button>
              <button
                onClick={() => handleMove('x', 1)}
                className="w-12 h-12 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center"
                title="Move Right (X+)"
              >
                →
              </button>

              {/* Bottom Row */}
              <div></div>
              <button
                onClick={() => handleMove('y', -1)}
                className="w-12 h-12 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center"
                title="Move Down (Y-)"
              >
                ↓
              </button>
              <div></div>
            </div>
          </div>

          {/* Z Movement */}
          <div className="z-movement flex flex-col items-center">
            <div className="text-xs mb-1 font-medium">Z Movement</div>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => handleMove('z', 1)}
                className="w-12 h-12 bg-purple-500 text-white rounded hover:bg-purple-600 flex items-center justify-center"
                title="Move Z Up"
              >
                Z+
              </button>
              <button
                onClick={() => handleMove('z', -1)}
                className="w-12 h-12 bg-purple-500 text-white rounded hover:bg-purple-600 flex items-center justify-center"
                title="Move Z Down"
              >
                Z-
              </button>
            </div>
          </div>
        </div>

        {/* Current Position Display */}
        <div className="text-xs text-gray-600 mt-2">
          Current Position: X: {position?.x?.toFixed(3) || '0.000'}, Y: {position?.y?.toFixed(3) || '0.000'}, Z: {position?.z?.toFixed(3) || '0.000'}
        </div>
      </div>

      {/* Goto XY */}
      <div className="goto-xy">
        <h3 className="text-sm font-medium mb-2">Goto XY</h3>
        <div className="flex gap-2 items-center">
          <input
            type="text"
            value={gotoX}
            onChange={(e) => setGotoX(e.target.value)}
            placeholder="X"
            className="p-1 border rounded w-24 text-sm"
          />
          <input
            type="text"
            value={gotoY}
            onChange={(e) => setGotoY(e.target.value)}
            placeholder="Y"
            className="p-1 border rounded w-24 text-sm"
          />
          <button
            onClick={handleGotoXY}
            className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          >
            Go
          </button>
        </div>
      </div>

      {/* Exposure Time */}
      <div className="exposure-control">
        <h3 className="text-sm font-medium mb-2">Camera Settings</h3>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 items-center">
            <label className="text-sm font-medium">Camera Index:</label>
            <input
              type="number"
              min="0"
              value={cameraIndex}
              onChange={(e) => setCameraIndex(Math.max(0, parseInt(e.target.value) || 0))}
              className="p-1 border rounded w-20 text-sm"
            />
          </div>
          <div className="flex gap-2 items-center">
            <label className="text-sm font-medium">Exposure (ms):</label>
            <input
              type="number"
              min="1"
              value={exposureTime}
              onChange={(e) => setExposureTime(Math.max(1, parseInt(e.target.value) || 100))}
              className="p-1 border rounded w-24 text-sm"
            />
            <button
              onClick={handleSetExposure}
              className="px-4 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            >
              Set
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
