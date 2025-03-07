import { useState, useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../state/jsonState";
import { useSendJSON } from "../hooks/useSendJSON";

interface Position {
  x: number;
  y: number;
  [key: string]: number | undefined;
}

const HeaderPositionDisplay = () => {
  const [position, setPosition] = useState<Position | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [pollRate, setPollRate] = useState(.3); // Default 5.0 times per second (200ms)
  const timerRef = useRef<number | null>(null);
  const initializedRef = useRef(false);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Function to fetch position
  const fetchPosition = () => {
    setLoading(true);
    sendJson({
      type: "REQUEST_POSITION"
    });
  };

  // Calculate polling interval in milliseconds
  const getPollInterval = () => {
    const safeRate = Math.max(0.1, Math.min(50, pollRate));
    return Math.round(1000 / safeRate);
  };

  // Clear any existing timer
  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // Start polling
  const startPolling = () => {
    if (!autoUpdate) return;
    
    clearTimer();
    
    const interval = getPollInterval();
    
    timerRef.current = window.setTimeout(() => {
      if (autoUpdate) {
        fetchPosition();
        startPolling();
      }
    }, interval);
  };

  // Initial setup when component mounts
  useEffect(() => {
    if (autoUpdate && !initializedRef.current) {
      initializedRef.current = true;
      fetchPosition();
      startPolling();
    }
    
    return () => {
      clearTimer();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle auto-update changes
  useEffect(() => {
    if (autoUpdate) {
      fetchPosition();
      startPolling();
    } else {
      clearTimer();
    }
    
    return () => {
      clearTimer();
    };
  }, [autoUpdate]);

  // Handle poll rate changes
  useEffect(() => {
    if (autoUpdate) {
      startPolling();
    }
  }, [pollRate]);

  // Process incoming position data
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;
    
    if (message.type === "POSITION" || message.type === "RESPONSE_POSITION") {
      if (typeof message.x === 'number' && typeof message.y === 'number') {
        const positionData: Position = {
          x: message.x,
          y: message.y
        };
        
        setPosition(positionData);
      }
      
      setLoading(false);
    }
  }, [jsonState.lastJsonMessage]);

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
    <div className="header-position-display flex items-center ml-4">
      <div className="flex items-center mr-3">
        <label className="flex items-center text-xs mr-2">
          <input
            type="checkbox"
            checked={autoUpdate}
            onChange={() => setAutoUpdate(!autoUpdate)}
            className="mr-1 h-3 w-3"
          />
          <span className="whitespace-nowrap">Auto</span>
        </label>
        
        <div className="flex items-center">
          <input
            type="number"
            min="0.1"
            max="50"
            step="0.1"
            value={pollRate.toFixed(1)}
            onChange={handlePollRateChange}
            disabled={!autoUpdate}
            className="w-10 h-5 text-xs px-1"
          />
          <span className="text-xs ml-1 whitespace-nowrap">
            Hz <span className="text-gray-300">({getPollInterval()}ms)</span>
          </span>
        </div>
      </div>
      
      <div className="position-values flex items-center text-xs">
        <div className="flex items-center mr-2">
          <span className="font-medium mr-1">X:</span>
          <span className={`${loading ? 'opacity-50' : ''}`}>
            {position ? formatPosition(position.x) : "0.000"}
          </span>
        </div>
        <div className="flex items-center">
          <span className="font-medium mr-1">Y:</span>
          <span className={`${loading ? 'opacity-50' : ''}`}>
            {position ? formatPosition(position.y) : "0.000"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HeaderPositionDisplay; 