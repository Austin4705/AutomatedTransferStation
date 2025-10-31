import { Outlet } from 'react-router-dom';
import ConnectionStatus from './ConnectionStatus';
import HeaderPositionDisplay from './HeaderPositionDisplay';
import HostConfigInput from './HostConfigInput';

const MainLayout = () => {
  const resetLayout = () => {
    if (window.confirm('Are you sure you want to reset the dashboard layout to default?')) {
      localStorage.removeItem('gridstack-layout');
      window.location.reload();
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="flex items-center">
          <div className="flex items-center">
            <h1>Automated Transfer Station</h1>
            <span className="mx-2 text-gray-300">|</span>
            <div className="flex flex-col" style={{ textAlign: 'left' }}>
              <span className="text-sm text-gray-300">Yasuda Lab - Cornell University</span>
              <span className="text-sm text-gray-300">by Austin Wu</span>
            </div>
          </div>
          <HostConfigInput />
          <HeaderPositionDisplay />
          <button
            onClick={resetLayout}
            className="ml-4 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm"
            title="Reset dashboard layout to default"
          >
            Reset Layout
          </button>
        </div>
        <ConnectionStatus />
      </header>

      <main className="app-content flex-1 p-4">
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout; 