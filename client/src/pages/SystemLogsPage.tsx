import UnifiedLog from '../components/UnifiedLog';

const SystemLogsPage = () => {
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