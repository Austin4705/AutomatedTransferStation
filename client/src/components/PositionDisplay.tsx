import { useState, useEffect, useRef } from "react";
import { usePositionContext } from "../state/positionContext";

const PositionDisplay = () => {
  const { 
    autoUpdate, 
    setAutoUpdate, 
    pollRate, 
    setPollRate, 
    position, 
    requestImmediateUpdate,
    isLoading 
  } = usePositionContext();

  // Calculate polling interval in milliseconds
  const getPollInterval = () => {
    // Ensure poll rate is between 0.1 and 50 times per second
    const safeRate = Math.max(0.1, Math.min(50, pollRate));
    return Math.round(1000 / safeRate); // Convert to milliseconds
  };

  // Handle poll rate change
  const handlePollRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value > 0) {
      setPollRate(value);
    }
  };

  const formatPosition = (value: number | undefined): string => {
    if (value === undefined) return "0.000";
    return value.toFixed(3);
  };

  return (
    <div className="position-display">
      <div className="position-controls mb-4">
        <div className="auto-update-toggle mb-2">
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={autoUpdate}
              onChange={() => {
                const newValue = !autoUpdate;
                setAutoUpdate(newValue);
                console.log("Auto-update toggled to:", newValue);
              }}
              className="mr-2"
            />
            Auto-update position
          </label>
          {autoUpdate && (
            <span className="text-xs text-green-500 ml-2">
              (Polling every {getPollInterval()}ms)
            </span>
          )}
        </div>
        
        <div className="poll-rate-control">
          <label className="text-sm block mb-1">
            Poll rate (times per second):
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0.1"
              max="50"
              step="0.1"
              value={pollRate.toFixed(1)}
              onChange={handlePollRateChange}
              disabled={!autoUpdate}
              className="poll-rate-input w-20"
            />
            <span className="text-sm text-gray-600">
              ({getPollInterval()}ms)
            </span>
          </div>
        </div>
      </div>
      
      {isLoading && (
        <div className="loading-indicator text-sm text-gray-600">
          Loading position data...
        </div>
      )}
      
      {position ? (
        <div className="position-data">
          <table className="position-table w-full text-sm">
            <tbody>
              {Object.entries(position).map(([axis, value]) => (
                <tr key={axis} className="position-row">
                  <td className="position-axis font-medium p-2">{axis.toUpperCase()}:</td>
                  <td className="position-value p-2">{formatPosition(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="no-position text-sm text-gray-600">
          No position data available
        </div>
      )}
      
      <div className="position-actions mt-2">
        <button 
          onClick={requestImmediateUpdate}
          className="refresh-button text-sm bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
          disabled={isLoading}
        >
          Refresh Position
        </button>
      </div>
    </div>
  );
};

export default PositionDisplay; 