import { useSendJSON } from "../../hooks/useSendJSON";
import { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";
import { positionSettingsAtom } from "../../state/appState";

interface Position {
  x: number;
  y: number;
}

const GotoFlakeBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const positionSettings = useRecoilValue(positionSettingsAtom);
  const position = positionSettings.currentPosition;

  const [imageId, setImageId] = useState<string>("");
  const [newStartX, setNewStartX] = useState<string>("");
  const [newStartY, setNewStartY] = useState<string>("");
  const [currentPosition, setCurrentPosition] = useState<Position>({ x: 0, y: 0 });
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error", message: string } | null>(null);

  // Update current position from atom
  useEffect(() => {
    if (position) {
      setCurrentPosition({
        x: position.x,
        y: position.y
      });
    }
  }, [position]);

  // Listen for response messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;

    if (message.type === "GOTO_FLAKE_RESULT") {
      if (message.success) {
        setStatusMessage({
          type: "success",
          message: message.message || "Successfully navigated to flake"
        });
      } else {
        setStatusMessage({
          type: "error",
          message: message.message || "Failed to navigate to flake"
        });
      }

      setTimeout(() => setStatusMessage(null), 5000);
    }
  }, [jsonState.lastJsonMessage]);

  const handleCoordinateChange = (
    axis: "x" | "y",
    value: string
  ) => {
    if (value !== "" && !/^-?\d*\.?\d*$/.test(value)) {
      return;
    }

    if (axis === "x") {
      setNewStartX(value);
    } else {
      setNewStartY(value);
    }
  };

  const copyCurrentPosition = () => {
    // Format the current position values
    const xValue = currentPosition.x.toFixed(3);
    const yValue = currentPosition.y.toFixed(3);

    setNewStartX(xValue);
    setNewStartY(yValue);
  };

  const handleGotoFlake = () => {
    // Validate inputs
    if (!imageId) {
      alert("Please enter an Image ID");
      return;
    }

    if (!newStartX || !newStartY) {
      alert("Please enter both X and Y coordinates");
      return;
    }

    const data = {
      type: "GOTO_FLAKE",
      image_id: imageId,
      new_start_x: parseFloat(newStartX),
      new_start_y: parseFloat(newStartY)
    };

    sendJson(data);
  };

  return (
    <div className="goto-flake-box p-4 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-3">Go to Flake</h3>

      {/* Status Message */}
      {statusMessage && (
        <div className={`mb-3 p-2 rounded ${
          statusMessage.type === "success"
            ? "bg-green-100 text-green-800"
            : "bg-red-100 text-red-800"
        }`}>
          {statusMessage.message}
        </div>
      )}

      {/* Image ID Input */}
      <div className="mb-4">
        <label className="text-sm font-medium mr-2">Image ID:</label>
        <input
          type="text"
          value={imageId}
          onChange={(e) => setImageId(e.target.value)}
          className="p-1 border rounded w-32 text-sm"
          placeholder="Enter image ID"
        />
      </div>

      {/* New Start Position */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-sm font-medium">New Start Position:</span>
        </div>
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={newStartX}
            onChange={(e) => handleCoordinateChange("x", e.target.value)}
            className="p-1 border rounded w-24 text-xs"
            placeholder="X"
          />
          <input
            type="text"
            value={newStartY}
            onChange={(e) => handleCoordinateChange("y", e.target.value)}
            className="p-1 border rounded w-24 text-xs"
            placeholder="Y"
          />
          <button
            onClick={copyCurrentPosition}
            className="px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded"
            title="Copy current position"
          >
            Use Current Position
          </button>
        </div>
      </div>

      {/* Current Position Display */}
      <div className="mb-4 text-xs text-gray-600">
        Current Position: X: {currentPosition.x.toFixed(3)}, Y: {currentPosition.y.toFixed(3)}
      </div>

      {/* Go to Flake Button */}
      <div className="flex justify-center">
        <button
          onClick={handleGotoFlake}
          disabled={!imageId || !newStartX || !newStartY}
          className={`${
            imageId && newStartX && newStartY
              ? "bg-purple-500 hover:bg-purple-600"
              : "bg-gray-300 cursor-not-allowed"
          } text-white px-4 py-2 rounded font-medium`}
        >
          Go to Flake
        </button>
      </div>
    </div>
  );
};

export default GotoFlakeBox;
