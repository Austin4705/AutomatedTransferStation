import { useState } from "react";
import { useRecoilState } from "recoil";
import { connectionStateAtom } from "../../state/appState";

const HostConfigInput = () => {
  const [connection, setConnection] = useRecoilState(connectionStateAtom);
  const [inputValue, setInputValue] = useState(connection.host);
  const [isEditing, setIsEditing] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Remove trailing slashes to prevent malformed URLs
    const sanitizedHost = inputValue.replace(/\/+$/, '');

    // Save to localStorage before updating state
    localStorage.setItem('connection-host', sanitizedHost);

    setConnection(prev => ({ ...prev, host: sanitizedHost }));
    setIsEditing(false);

    window.location.reload();
  };

  const handleCancel = () => {
    setInputValue(connection.host);
    setIsEditing(false);
  };

  return (
    <div className="host-config-input">
      {isEditing ? (
        <form onSubmit={handleSubmit} className="host-config-form">
          <label className="text-sm text-gray-300">Host:</label>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="127.0.0.1"
            className="host-config-text-input"
            autoFocus
          />
          <button
            type="submit"
            className="host-config-button host-config-apply"
          >
            Apply
          </button>
          <button
            type="button"
            onClick={handleCancel}
            className="host-config-button host-config-cancel"
          >
            Cancel
          </button>
        </form>
      ) : (
        <div className="host-config-readonly">
          <span className="host-config-host-label">
            Host: <span className="font-mono font-semibold">{connection.host}</span>
          </span>
          <button
            onClick={() => setIsEditing(true)}
            className="host-config-button host-config-change"
          >
            Change
          </button>
        </div>
      )}
    </div>
  );
};

export default HostConfigInput;
