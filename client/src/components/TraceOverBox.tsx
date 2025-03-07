import { useSendJSON } from "../hooks/useSendJSON";

const TraceOverBox = () => {
  const sendJson = useSendJSON();

  const handleTraceOver = (command: string) => {
    sendJson({
      type: "TRACE_OVER",
      command
    });
  };

  return (
    <div className="trace-over-box">
      <h2>Trace Over</h2>
      <div className="trace-container">
        <div className="trace-input-group flex gap-2">
          <input
            type="text"
            placeholder="Trace command (coming soon)"
            className="trace-input flex-grow"
            disabled
          />
          <button 
            className="trace-button"
            disabled
            onClick={() => handleTraceOver("trace")}
          >
            Trace
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          Trace functionality will be implemented soon
        </p>
      </div>
    </div>
  );
};

export default TraceOverBox; 