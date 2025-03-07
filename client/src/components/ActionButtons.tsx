import { useSendJSON } from "../hooks/useSendJSON";

const ActionButtons = () => {
  const sendJson = useSendJSON();

  const handleSnap = (snapNumber: number) => {
    sendJson({
      type: "SNAP_SHOT",
      camera: snapNumber
    });
  };

  return (
    <div className="action-buttons">
      <div className="button-group flex flex-wrap gap-2">
        <button 
          onClick={() => handleSnap(0)}
          className="snap-button"
        >
          Snap 0
        </button>
        
        <button 
          onClick={() => handleSnap(1)}
          className="snap-button"
        >
          Snap 1
        </button>
        
        <button 
          onClick={() => handleSnap(2)}
          className="snap-button"
        >
          Snap 2
        </button>
      </div>
      
      <div className="trace-container mt-4">
        <h3 className="text-sm font-medium mb-2">Trace Over Command</h3>
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

export default ActionButtons; 