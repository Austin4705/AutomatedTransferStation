import ActionsBox from '../components/dashboard/ActionsBox';
import CommandInputBox from '../components/dashboard/CommandInputBox';
import TransferStationCommandsBox from '../components/dashboard/TransferStationCommandsBox';
import PacketInputBox from '../components/dashboard/PacketInputBox';

const CommandsPage = () => {
  return (
    <div className="commands-page">
      <div className="commands-section">
        <div className="action-container">
          <h2>Actions</h2>
          <ActionsBox />
        </div>
        
        <div className="input-container mt-6">
          <div className="command-input mb-4">
            <h2>Command Input</h2>
            <CommandInputBox />
          </div>
          
          <div className="ts-command-input mb-4">
            <h2>Transfer Station Commands</h2>
            <TransferStationCommandsBox />
          </div>
          
          <div className="packet-input mb-4">
            <h2>Packet Input</h2>
            <PacketInputBox />
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommandsPage; 