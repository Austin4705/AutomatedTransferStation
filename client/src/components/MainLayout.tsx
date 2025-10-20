import { Outlet } from 'react-router-dom';
import ConnectionStatus from './ConnectionStatus';
import HeaderPositionDisplay from './HeaderPositionDisplay';
import Navigation from './Navigation';

const MainLayout = () => {
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
          <HeaderPositionDisplay />
        </div>
        <ConnectionStatus />
      </header>
      
      <Navigation />
      
      <main className="app-content flex-1 p-4">
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout; 