import ActionButtons from '../components/ActionButtons';
import CommandInput from '../components/CommandInput';
import TransferStationCommandInput from '../components/TransferStationCommandInput';
import PacketInput from '../components/PacketInput';

const CommandsPage = () => {
  return (
    <div className="commands-page">
      <div className="commands-section">
        <div className="action-container">
          <h2>Actions</h2>
          <ActionButtons />
        </div>
        
        <div className="input-container mt-6">
          <div className="command-input mb-4">
            <h2>Command Input</h2>
            <CommandInput />
          </div>
          
          <div className="ts-command-input mb-4">
            <h2>Transfer Station Commands</h2>
            <TransferStationCommandInput />
          </div>
          
          <div className="packet-input mb-4">
            <h2>Packet Input</h2>
            <PacketInput />
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommandsPage; 