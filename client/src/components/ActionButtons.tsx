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
    </div>
  );
};

export default ActionButtons; 