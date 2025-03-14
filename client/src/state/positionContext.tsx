import React, { createContext, useContext, useState, useEffect } from 'react';

// Define the context interface
interface PositionContextType {
  autoUpdate: boolean;
  setAutoUpdate: (value: boolean) => void;
  pollRate: number;
  setPollRate: (value: number) => void;
}

// Create the context with default values
const PositionContext = createContext<PositionContextType>({
  autoUpdate: true,
  setAutoUpdate: () => {},
  pollRate: 1.0,
  setPollRate: () => {}
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

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('position-auto-update', autoUpdate.toString());
  }, [autoUpdate]);

  useEffect(() => {
    localStorage.setItem('position-poll-rate', pollRate.toString());
  }, [pollRate]);

  return (
    <PositionContext.Provider value={{ autoUpdate, setAutoUpdate, pollRate, setPollRate }}>
      {children}
    </PositionContext.Provider>
  );
};

// Create a hook for using the context
export const usePositionContext = () => useContext(PositionContext); 