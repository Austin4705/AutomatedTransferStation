import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";
import { usePositionContext } from "../state/positionContext";

interface Position {
  x: number;
  y: number;
  z?: number; // Make z optional
  [key: string]: number | undefined; // For any additional axes
}

const PositionDisplay = () => {
  const [position, setPosition] = useState<Position | null>(null);
  const [loading, setLoading] = useState(false);
  const { autoUpdate, setAutoUpdate, pollRate, setPollRate } = usePositionContext();
  const [requestError, setRequestError] = useState(false); // Track position request errors
  const timerRef = useRef<number | null>(null);
  const initializedRef = useRef(false); // Track if polling has been initialized
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Function to fetch position
  const fetchPosition = () => {
    console.log("Fetching position...");
    setLoading(true);
    setRequestError(false);
    sendJson({
      type: "REQUEST_POSITION"
    });
  };

  // Calculate polling interval in milliseconds
  const getPollInterval = () => {
    // Ensure poll rate is between 0.1 and 50 times per second
    const safeRate = Math.max(0.1, Math.min(50, pollRate));
    return Math.round(1000 / safeRate); // Convert to milliseconds
  };

  // Clear any existing timer
  const clearTimer = () => {
    if (timerRef.current !== null) {
      console.log("Clearing existing timer");
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // Start polling
  const startPolling = () => {
    if (!autoUpdate) return;
    
    clearTimer();
    
    const interval = getPollInterval();
    console.log(`Starting polling with interval: ${interval}ms`);
    
    // Schedule the next poll
    timerRef.current = window.setTimeout(() => {
      if (autoUpdate) {
        fetchPosition();
        // After fetching, start polling again
        startPolling();
      }
    }, interval);
  };

  // Initial setup when component mounts
  useEffect(() => {
    console.log("Component mounted, initializing polling");
    if (autoUpdate && !initializedRef.current) {
      initializedRef.current = true;
      // Fetch immediately
      fetchPosition();
      // Start polling
      startPolling();
    }
    
    // Clean up on unmount
    return () => {
      clearTimer();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array means this runs once on mount

  // Handle auto-update changes
  useEffect(() => {
    console.log("Auto-update changed:", autoUpdate);
    
    if (autoUpdate) {
      // Fetch immediately when auto-update is turned on
      fetchPosition();
      // Start polling
      startPolling();
    } else {
      // Clear timer when auto-update is turned off
      clearTimer();
    }
    
    // Clean up on unmount
    return () => {
      clearTimer();
    };
  }, [autoUpdate]);

  // Handle poll rate changes
  useEffect(() => {
    if (autoUpdate) {
      console.log("Poll rate changed, restarting polling");
      // Restart polling with new rate
      startPolling();
    }
  }, [pollRate]);

  // Process incoming position data
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;
    
    // Handle both POSITION and RESPONSE_POSITION types
    if (message.type === "POSITION" || message.type === "RESPONSE_POSITION") {
      console.log("Received position data:", message);
      
      // Check if we have valid position data
      if (typeof message.x === 'number' && typeof message.y === 'number') {
        // Extract position data directly from the message (only x and y)
        const positionData: Position = {
          x: message.x,
          y: message.y
        };
        
        // Add any additional axes that might be present (except z)
        Object.keys(message).forEach(key => {
          if (key !== "type" && key !== "x" && key !== "y" && key !== "z" && typeof message[key] === "number") {
            positionData[key] = message[key];
          }
        });
        
        setPosition(positionData);
      } else {
        console.warn("Invalid position data received:", message);
      }
      
      setLoading(false);
    } else if (message.type === "ERROR" && loading) {
      // Handle error response related to position requests
      console.error("Position request error:", message);
      setLoading(false);
      setRequestError(true);
    }
  }, [jsonState.lastJsonMessage, loading]);

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
      
      {loading && (
        <div className="loading-indicator text-sm text-gray-600">
          Loading position data...
        </div>
      )}
      
      {requestError && (
        <div className="error-indicator text-sm text-red-600 mb-2">
          Error fetching position data. Will retry on next interval.
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
          onClick={fetchPosition}
          className="refresh-button text-sm bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh Position"}
        </button>
      </div>
    </div>
  );
};

export default PositionDisplay; 