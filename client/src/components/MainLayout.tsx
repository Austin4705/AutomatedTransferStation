import { Outlet } from 'react-router-dom';
import ConnectionStatus from './ConnectionStatus';
import HeaderPositionDisplay from './HeaderPositionDisplay';
import Navigation from './Navigation';

const MainLayout = () => {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="flex items-center">
          <h1>Automated Transfer Station</h1>
          <HeaderPositionDisplay />
        </div>
        <ConnectionStatus />
      </header>
      
      <Navigation />
      
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout; 