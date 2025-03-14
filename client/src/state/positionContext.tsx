import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useSendJSON } from '../hooks/useSendJSON';
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "./jsonState";
import { ReadyState } from "react-use-websocket";

// Define the context interface
interface PositionContextType {
  autoUpdate: boolean;
  setAutoUpdate: (value: boolean) => void;
  pollRate: number;
  setPollRate: (value: number) => void;
  position: Position | null;
  requestImmediateUpdate: () => void;
  isLoading: boolean;
}

// Define Position interface
interface Position {
  x: number;
  y: number;
  z?: number;
  [key: string]: number | undefined;
}

// Create the context with default values
const PositionContext = createContext<PositionContextType>({
  autoUpdate: true,
  setAutoUpdate: () => {},
  pollRate: 1.0,
  setPollRate: () => {},
  position: null,
  requestImmediateUpdate: () => {},
  isLoading: false
});

// Create a provider component
export const PositionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [autoUpdate, setAutoUpdate] = useState<boolean>(() => {
    // Try to get the setting from localStorage, default to true
    const savedSetting = localStorage.getItem('position-auto-update');
    return savedSetting !== null ? savedSetting === 'true' : true;
  });
  
  const [pollRate, setPollRate] = useState<number>(() => {
    // Try to get the setting from localStorage, default to 1.0Hz
    const savedRate = localStorage.getItem('position-poll-rate');
    return savedRate !== null ? parseFloat(savedRate) : 1.0;
  });

  const [position, setPosition] = useState<Position | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const timerRef = useRef<number | null>(null);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('position-auto-update', autoUpdate.toString());
  }, [autoUpdate]);

  useEffect(() => {
    localStorage.setItem('position-poll-rate', pollRate.toString());
  }, [pollRate]);

  // Function to fetch position
  const fetchPosition = () => {
    // Only send the request if the websocket is open
    if (jsonState.readyState === ReadyState.OPEN) {
      // console.log("Context: Fetching position...");
      setIsLoading(true);
      sendJson({
        type: "REQUEST_POSITION"
      });
    } else {
      console.warn("WebSocket not connected. Position request not sent.");
      setIsLoading(false);
    }
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
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // Start polling
  const startPolling = () => {
    if (!autoUpdate) return;
    
    clearTimer();
    
    const interval = getPollInterval();
    
    // Schedule the next poll
    timerRef.current = window.setTimeout(() => {
      if (autoUpdate) {
        fetchPosition();
        // After fetching, start polling again
        startPolling();
      }
    }, interval);
  };

  // Handle auto-update changes
  useEffect(() => {
    console.log("Position context: Auto-update changed:", autoUpdate);
    
    if (autoUpdate) {
      // Only start if the connection is open
      if (jsonState.readyState === ReadyState.OPEN) {
        console.log("WebSocket is open, starting position polling");
        // Fetch immediately when auto-update is turned on
        fetchPosition();
        // Start polling
        startPolling();
      } else {
        console.log("WebSocket not ready, waiting for connection...");
      }
    } else {
      // Clear timer when auto-update is turned off
      clearTimer();
    }
    
    // Clean up on unmount
    return () => {
      clearTimer();
    };
  }, [autoUpdate, jsonState.readyState]);

  // Watch for WebSocket connection changes
  useEffect(() => {
    if (jsonState.readyState === ReadyState.OPEN && autoUpdate) {
      console.log("WebSocket connected, starting position polling");
      // Start polling once connection is established
      fetchPosition();
      startPolling();
    }
  }, [jsonState.readyState]);

  // Handle poll rate changes
  useEffect(() => {
    if (autoUpdate) {
      console.log("Position context: Poll rate changed, restarting polling");
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
      // Check if we have valid position data
      if (typeof message.x === 'number' && typeof message.y === 'number') {
        // Extract position data
        const positionData: Position = {
          x: message.x,
          y: message.y
        };
        
        // Handle z-axis if present
        if (typeof message.z === 'number') {
          positionData.z = message.z;
        }
        
        // Add any additional axes that might be present
        Object.keys(message).forEach(key => {
          if (key !== "type" && key !== "x" && key !== "y" && key !== "z" && typeof message[key] === "number") {
            positionData[key] = message[key];
          }
        });
        
        setPosition(positionData);
      }
      
      setIsLoading(false);
    }
  }, [jsonState.lastJsonMessage]);

  // Public function to request immediate position update
  const requestImmediateUpdate = () => {
    fetchPosition();
  };

  return (
    <PositionContext.Provider value={{ 
      autoUpdate, 
      setAutoUpdate, 
      pollRate, 
      setPollRate, 
      position, 
      requestImmediateUpdate,
      isLoading
    }}>
      {children}
    </PositionContext.Provider>
  );
};

// Create a hook for using the context
export const usePositionContext = () => useContext(PositionContext); 