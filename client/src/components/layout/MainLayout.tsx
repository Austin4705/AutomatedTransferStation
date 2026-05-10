import { Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import ConnectionStatus from './ConnectionStatus';
import HeaderPositionDisplay from './HeaderPositionDisplay';
import HostConfigInput from './HostConfigInput';
import { connectionStateAtom } from '../../state/appState';
import {
  dashboardLayoutConfigAtom,
  DEFAULT_DASHBOARD_LAYOUT,
  GridLayoutItem,
  gridLayoutAtom,
} from '../../state/gridLayoutState';

const cloneLayout = (layout: GridLayoutItem[]): GridLayoutItem[] =>
  layout.map((item) => ({ ...item }));

const MainLayout = () => {
  const connection = useRecoilValue(connectionStateAtom);
  const [gridLayout, setGridLayout] = useRecoilState(gridLayoutAtom);
  const [dashboardConfig, setDashboardConfig] = useRecoilState(dashboardLayoutConfigAtom);
  const [isSavingLayout, setIsSavingLayout] = useState(false);
  const [isResettingLayout, setIsResettingLayout] = useState(false);

  const configBaseUrl = `http://${connection.host}:3000`;

  useEffect(() => {
    const loadDashboardLayout = async () => {
      try {
        const response = await fetch(`${configBaseUrl}/dashboard_layout_config`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json() as { layout?: GridLayoutItem[] };
        const loadedLayout = Array.isArray(payload.layout) && payload.layout.length > 0
          ? payload.layout
          : DEFAULT_DASHBOARD_LAYOUT;
        const initialLayout = cloneLayout(loadedLayout);

        setGridLayout(cloneLayout(initialLayout));
        setDashboardConfig({
          initialLayout,
          isLoaded: true,
        });
      } catch (error) {
        console.error('Failed to load dashboard layout config, using defaults:', error);
        const fallbackLayout = cloneLayout(DEFAULT_DASHBOARD_LAYOUT);
        setGridLayout(cloneLayout(fallbackLayout));
        setDashboardConfig({
          initialLayout: fallbackLayout,
          isLoaded: true,
        });
      }
    };

    loadDashboardLayout();
  }, [configBaseUrl, setDashboardConfig, setGridLayout]);

  const resetLayout = async () => {
    if (!window.confirm('Are you sure you want to reset the dashboard layout from Data/dashboard_layout_config.json?')) {
      return;
    }

    setIsResettingLayout(true);
    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layout_config`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json() as { layout?: GridLayoutItem[] };
      const loadedLayout = Array.isArray(payload.layout) && payload.layout.length > 0
        ? payload.layout
        : DEFAULT_DASHBOARD_LAYOUT;
      const resetLayoutValue = cloneLayout(loadedLayout);

      setGridLayout(cloneLayout(resetLayoutValue));
      setDashboardConfig({
        initialLayout: resetLayoutValue,
        isLoaded: true,
      });
    } catch (error) {
      console.error('Failed to reset dashboard layout from backend config:', error);
      const fallbackLayout = dashboardConfig.initialLayout.length > 0
        ? dashboardConfig.initialLayout
        : DEFAULT_DASHBOARD_LAYOUT;
      setGridLayout(cloneLayout(fallbackLayout));
      window.alert('Failed to fetch Data/dashboard_layout_config.json from backend. Reset to last loaded layout.');
    } finally {
      setIsResettingLayout(false);
    }
  };

  const saveLayout = async () => {
    setIsSavingLayout(true);
    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layout_config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ layout: gridLayout }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json() as { layout?: GridLayoutItem[] };
      const persistedLayout = Array.isArray(payload.layout) && payload.layout.length > 0
        ? payload.layout
        : cloneLayout(gridLayout);

      setDashboardConfig({
        initialLayout: cloneLayout(persistedLayout),
        isLoaded: true,
      });
      window.alert('Dashboard layout saved to Data/dashboard_layout_config.json');
    } catch (error) {
      console.error('Failed to save dashboard layout:', error);
      window.alert('Failed to save dashboard layout config.');
    } finally {
      setIsSavingLayout(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header overflow-x-auto">
        <div className="flex items-center min-w-max">
          <div className="flex items-center flex-shrink-0">
            <h1 className="whitespace-nowrap">Automated Transfer Station</h1>
            <span className="mx-2 text-gray-300">|</span>
            <div className="flex flex-col whitespace-nowrap" style={{ textAlign: 'left' }}>
              <span className="text-sm text-gray-300">Yasuda Lab - Cornell University</span>
              <span className="text-sm text-gray-300">by Austin Wu</span>
            </div>
          </div>
          <HostConfigInput />
          <HeaderPositionDisplay />
          <button
            onClick={resetLayout}
            disabled={!dashboardConfig.isLoaded || isResettingLayout}
            className="ml-4 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm flex-shrink-0 whitespace-nowrap disabled:bg-gray-500 disabled:cursor-not-allowed"
            title="Reset dashboard layout from Data/dashboard_layout_config.json"
          >
            {isResettingLayout ? 'Resetting...' : 'Reset Layout'}
          </button>
          <button
            onClick={saveLayout}
            disabled={isSavingLayout || !dashboardConfig.isLoaded}
            className="ml-2 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm flex-shrink-0 whitespace-nowrap disabled:bg-gray-500 disabled:cursor-not-allowed"
            title="Save current dashboard layout to Data/dashboard_layout_config.json"
          >
            {isSavingLayout ? 'Saving...' : 'Save Layout'}
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
