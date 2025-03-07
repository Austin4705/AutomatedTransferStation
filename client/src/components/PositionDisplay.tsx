import { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";

interface Position {
  x: number;
  y: number;
  z: number;
  [key: string]: number; // For any additional axes
}

const PositionDisplay = () => {
  const [position, setPosition] = useState<Position | null>(null);
  const [loading, setLoading] = useState(false);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Request position on component mount and periodically
  useEffect(() => {
    const fetchPosition = () => {
      setLoading(true);
      sendJson({
        type: "REQUEST_POSITION"
      });
    };

    fetchPosition();
    
    // Set up a periodic refresh every 500ms (1/2 second)
    const intervalId = setInterval(fetchPosition, 500);
    
    return () => clearInterval(intervalId);
  }, [sendJson]);

  // Process incoming position data
  useEffect(() => {
    if (
      jsonState.lastJsonMessage && 
      jsonState.lastJsonMessage.type === "RESPONSE_POSITION"
    ) {
      setPosition(jsonState.lastJsonMessage.position || {});
      setLoading(false);
    }
  }, [jsonState.lastJsonMessage]);

  const formatPosition = (value: number): string => {
    return value.toFixed(3);
  };

  return (
    <div className="position-display">
      {loading && !position && (
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
          onClick={() => {
            setLoading(true);
            sendJson({ type: "REQUEST_POSITION" });
          }}
          className="refresh-button text-sm"
        >
          Refresh Position
        </button>
      </div>
    </div>
  );
};

export default PositionDisplay; 