import { useEffect, useRef } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import { positionSettingsAtom } from '../state/appState';
import { jsonStateAtom } from '../state/jsonState';
import { useSendJSON } from './useSendJSON';
import { ReadyState } from 'react-use-websocket';

/**
 * Hook to manage automatic position polling
 * Sends REQUEST_STATE packets at configured intervals when autoUpdate is enabled
 */
export const usePositionPolling = () => {
  const [positionSettings, setPositionSettings] = useRecoilState(positionSettingsAtom);
  const jsonState = useRecoilValue(jsonStateAtom);
  const sendJson = useSendJSON();
  const timerRef = useRef<number | null>(null);

  // Calculate polling interval in milliseconds
  const getPollInterval = () => {
    // Ensure poll rate is between 0.1 and 50 times per second
    const safeRate = Math.max(0.1, Math.min(50, positionSettings.pollRate));
    return Math.round(1000 / safeRate); // Convert to milliseconds
  };

  // Function to fetch position
  const fetchPosition = () => {
    // Only send the request if the websocket is open
    if (jsonState.readyState === ReadyState.OPEN) {
      setPositionSettings(prev => ({ ...prev, isLoading: true }));
      sendJson({
        type: "REQUEST_STATE"
      });
    } else {
      setPositionSettings(prev => ({ ...prev, isLoading: false }));
    }
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
    if (!positionSettings.autoUpdate) return;

    clearTimer();

    const interval = getPollInterval();

    // Schedule the next poll
    timerRef.current = window.setTimeout(() => {
      if (positionSettings.autoUpdate) {
        fetchPosition();
        // After fetching, start polling again
        startPolling();
      }
    }, interval);
  };

  // Handle auto-update changes
  useEffect(() => {
    if (positionSettings.autoUpdate) {
      // Only start if the connection is open
      if (jsonState.readyState === ReadyState.OPEN) {
        // Fetch immediately when auto-update is turned on
        fetchPosition();
        // Start polling
        startPolling();
      }
    } else {
      // Clear timer when auto-update is turned off
      clearTimer();
    }

    // Clean up on unmount
    return () => {
      clearTimer();
    };
  }, [positionSettings.autoUpdate, jsonState.readyState]);

  // Watch for WebSocket connection changes
  useEffect(() => {
    if (jsonState.readyState === ReadyState.OPEN && positionSettings.autoUpdate) {
      // Start polling once connection is established
      fetchPosition();
      startPolling();
    }
  }, [jsonState.readyState]);

  // Handle poll rate changes
  useEffect(() => {
    if (positionSettings.autoUpdate) {
      // Restart polling with new rate
      startPolling();
    }
  }, [positionSettings.pollRate]);

  // Listen for position updates from packet handlers
  useEffect(() => {
    const handlePositionUpdate = (event: CustomEvent) => {
      const { position } = event.detail;
      setPositionSettings(prev => ({
        ...prev,
        currentPosition: position,
        isLoading: false
      }));
    };

    window.addEventListener('position-update', handlePositionUpdate as EventListener);

    return () => {
      window.removeEventListener('position-update', handlePositionUpdate as EventListener);
    };
  }, [setPositionSettings]);

  // Public function to request immediate position update
  const requestImmediateUpdate = () => {
    fetchPosition();
  };

  return {
    requestImmediateUpdate
  };
};
