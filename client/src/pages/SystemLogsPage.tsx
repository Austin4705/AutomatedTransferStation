import { useEffect } from 'react';
import UnifiedLog from '../components/UnifiedLog';

const SystemLogsPage = () => {
  // When the page mounts, dispatch an event to disable logs
  useEffect(() => {
    // Dispatch event to disable command and response logs by default
    const event = new CustomEvent('logs-visibility-changed', { 
      detail: { 
        commandLogs: false,
        responseLogs: false,
      } 
    });
    document.dispatchEvent(event);

    // Re-enable logs when component unmounts
    return () => {
      const resetEvent = new CustomEvent('logs-visibility-changed', { 
        detail: { 
          commandLogs: true,
          responseLogs: true,
        } 
      });
      document.dispatchEvent(resetEvent);
    };
  }, []);

  return (
    <div className="system-logs-page">
      <div className="log-section">
        <div className="log-container full-width">
          <h2>System Logs</h2>
          <UnifiedLog />
        </div>
      </div>
    </div>
  );
}

export default SystemLogsPage; 