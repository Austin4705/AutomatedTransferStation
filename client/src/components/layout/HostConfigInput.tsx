import { useState } from "react";
import { useRecoilState } from "recoil";
import { connectionStateAtom } from "../../state/appState";

const HostConfigInput = () => {
  const [connection, setConnection] = useRecoilState(connectionStateAtom);
  const [inputValue, setInputValue] = useState(connection.host);
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Save to localStorage before updating state
    localStorage.setItem('connection-host', inputValue);

    setConnection(prev => ({ ...prev, host: inputValue }));
    setIsEditing(false);

    window.location.reload();
  };

  const handleCancel = () => {
    setInputValue(connection.host);
    setIsEditing(false);
  };

  return (
    <div className="host-config-input flex items-center gap-2 ml-4">
      {isEditing ? (
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <label className="text-sm text-gray-300">Host:</label>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="127.0.0.1"
            className="px-2 py-1 text-sm rounded border border-gray-300 bg-white text-gray-900"
            style={{ width: "150px" }}
            autoFocus
          />
          <button
            type="submit"
            className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
          >
            Apply
          </button>
          <button
            type="button"
            onClick={handleCancel}
            className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Cancel
          </button>
        </form>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-300">
            Host: <span className="font-mono font-semibold">{connection.host}</span>
          </span>
          <button
            onClick={() => setIsEditing(true)}
            className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Change
          </button>
        </div>
      )}
    </div>
  );
};

export default HostConfigInput;

