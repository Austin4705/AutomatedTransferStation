import { Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import ConnectionStatus from './ConnectionStatus';
import HeaderPositionDisplay from './HeaderPositionDisplay';
import HostConfigInput from './HostConfigInput';
import { connectionStateAtom } from '../../state/appState';
import {
  dashboardLayoutConfigAtom,
  GridLayoutItem,
  gridLayoutAtom,
  SavedDashboardLayout,
} from '../../state/gridLayoutState';

const LEGACY_LAYOUT_TYPES: Record<string, string> = {
  'camera-1': 'camera',
  'camera-2': 'camera',
  'trace-over': 'trace-over',
  'scan-flakes': 'scan-flakes',
  'goto-flake': 'goto-flake',
  commands: 'commands',
  'control-panel': 'control-panel',
  'trace-over-area': 'trace-over-area',
  packets: 'packets',
  logs: 'logs',
};

const cloneLayout = (layout: GridLayoutItem[]): GridLayoutItem[] =>
  layout.map((item) => ({ ...item }));

const normalizeLayout = (layout: GridLayoutItem[] | undefined): GridLayoutItem[] => {
  if (!Array.isArray(layout)) {
    return [];
  }

  return layout.map((item) => ({
    ...item,
    type: item.type || LEGACY_LAYOUT_TYPES[item.id] || item.id,
  }));
};

const MainLayout = () => {
  const connection = useRecoilValue(connectionStateAtom);
  const [gridLayout, setGridLayout] = useRecoilState(gridLayoutAtom);
  const [dashboardConfig, setDashboardConfig] = useRecoilState(dashboardLayoutConfigAtom);
  const [layoutName, setLayoutName] = useState('');
  const [isSavingLayout, setIsSavingLayout] = useState(false);
  const [isLoadingLayouts, setIsLoadingLayouts] = useState(false);

  const configBaseUrl = `http://${connection.host}:3000`;
  const activeLayout = dashboardConfig.savedLayouts.find((layout) => layout.id === dashboardConfig.activeLayoutId);

  const refreshSavedLayouts = async () => {
    setIsLoadingLayouts(true);
    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layouts`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json() as { layouts?: SavedDashboardLayout[] };
      const savedLayouts = Array.isArray(payload.layouts)
        ? payload.layouts.map((layout) => ({
          ...layout,
          layout: normalizeLayout(layout.layout),
        }))
        : [];

      setDashboardConfig((current) => ({
        ...current,
        savedLayouts,
        isLoaded: true,
      }));
    } catch (error) {
      console.error('Failed to load dashboard layouts:', error);
      setDashboardConfig((current) => ({
        ...current,
        savedLayouts: [],
        activeLayoutId: null,
        isLoaded: true,
      }));
    } finally {
      setIsLoadingLayouts(false);
    }
  };

  useEffect(() => {
    setGridLayout([]);
    setDashboardConfig({
      initialLayout: [],
      savedLayouts: [],
      activeLayoutId: null,
      isLoaded: false,
    });
    refreshSavedLayouts();
  }, [configBaseUrl, setDashboardConfig, setGridLayout]);

  const resetLayout = () => {
    setGridLayout([]);
    setLayoutName('');
    setDashboardConfig((current) => ({
      ...current,
      initialLayout: [],
      activeLayoutId: null,
    }));
  };

  const loadLayout = (layout: SavedDashboardLayout) => {
    const normalizedLayout = normalizeLayout(layout.layout);
    setGridLayout(cloneLayout(normalizedLayout));
    setLayoutName(layout.name);
    setDashboardConfig((current) => ({
      ...current,
      initialLayout: cloneLayout(normalizedLayout),
      activeLayoutId: layout.id,
    }));
  };

  const saveLayout = async () => {
    const name = layoutName.trim() || activeLayout?.name || window.prompt('Layout name')?.trim();
    if (!name) {
      return;
    }

    setIsSavingLayout(true);
    try {
      const activeLayoutId = dashboardConfig.activeLayoutId;
      const response = await fetch(
        activeLayoutId ? `${configBaseUrl}/dashboard_layouts/${activeLayoutId}` : `${configBaseUrl}/dashboard_layouts`,
        {
          method: activeLayoutId ? 'PUT' : 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ name, layout: gridLayout }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json() as {
        layout_config?: SavedDashboardLayout;
        layouts?: SavedDashboardLayout[];
      };
      const savedLayouts = Array.isArray(payload.layouts)
        ? payload.layouts.map((layout) => ({
          ...layout,
          layout: normalizeLayout(layout.layout),
        }))
        : dashboardConfig.savedLayouts;
      const savedLayout = payload.layout_config;

      setDashboardConfig((current) => ({
        ...current,
        savedLayouts,
        initialLayout: cloneLayout(gridLayout),
        activeLayoutId: savedLayout?.id || activeLayoutId,
        isLoaded: true,
      }));
      setLayoutName(savedLayout?.name || name);
    } catch (error) {
      console.error('Failed to save dashboard layout:', error);
      window.alert('Failed to save dashboard layout.');
    } finally {
      setIsSavingLayout(false);
    }
  };

  const renameLayout = async (layout: SavedDashboardLayout) => {
    const name = window.prompt('Rename layout', layout.name)?.trim();
    if (!name || name === layout.name) {
      return;
    }

    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layouts/${layout.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json() as { layouts?: SavedDashboardLayout[] };
      const savedLayouts = Array.isArray(payload.layouts) ? payload.layouts : dashboardConfig.savedLayouts;
      setDashboardConfig((current) => ({ ...current, savedLayouts }));
      if (dashboardConfig.activeLayoutId === layout.id) {
        setLayoutName(name);
      }
    } catch (error) {
      console.error('Failed to rename dashboard layout:', error);
      window.alert('Failed to rename layout.');
    }
  };

  const duplicateLayout = async (layout: SavedDashboardLayout) => {
    const name = window.prompt('Duplicate layout as', `${layout.name} Copy`)?.trim();
    if (!name) {
      return;
    }

    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layouts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, layout: layout.layout }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json() as { layouts?: SavedDashboardLayout[] };
      const savedLayouts = Array.isArray(payload.layouts) ? payload.layouts : dashboardConfig.savedLayouts;
      setDashboardConfig((current) => ({ ...current, savedLayouts }));
    } catch (error) {
      console.error('Failed to duplicate dashboard layout:', error);
      window.alert('Failed to duplicate layout.');
    }
  };

  const deleteLayout = async (layout: SavedDashboardLayout) => {
    if (!window.confirm(`Delete layout "${layout.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${configBaseUrl}/dashboard_layouts/${layout.id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json() as { layouts?: SavedDashboardLayout[] };
      const savedLayouts = Array.isArray(payload.layouts) ? payload.layouts : [];
      setDashboardConfig((current) => ({
        ...current,
        savedLayouts,
        activeLayoutId: current.activeLayoutId === layout.id ? null : current.activeLayoutId,
        initialLayout: current.activeLayoutId === layout.id ? [] : current.initialLayout,
      }));
      if (dashboardConfig.activeLayoutId === layout.id) {
        setGridLayout([]);
        setLayoutName('');
      }
    } catch (error) {
      console.error('Failed to delete dashboard layout:', error);
      window.alert('Failed to delete layout.');
    }
  };

  return (
    <div className="app-container">
      <header className="app-header app-header-layout">
        <div className="header-primary-row">
          <div className="header-brand">
            <h1 className="whitespace-nowrap">Automated Transfer Station</h1>
            <span className="mx-2 text-gray-300">|</span>
            <div className="flex flex-col whitespace-nowrap" style={{ textAlign: 'left' }}>
              <span className="text-sm text-gray-300">Yasuda Lab - Cornell University</span>
              <span className="text-sm text-gray-300">by Austin Wu</span>
            </div>
          </div>
          <div className="header-controls">
            <HostConfigInput />
            <HeaderPositionDisplay />
            <ConnectionStatus />
          </div>
        </div>

        <div className="dashboard-layout-shelf">
          <div className="layout-save-controls">
            <input
              value={layoutName}
              onChange={(event) => setLayoutName(event.target.value)}
              className="layout-name-input"
              placeholder="Layout name"
            />
            <button
              onClick={saveLayout}
              disabled={isSavingLayout || !dashboardConfig.isLoaded}
              className="layout-action-button layout-save-button"
              title="Save current dashboard layout on the server"
            >
              {isSavingLayout ? 'Saving...' : activeLayout ? 'Save' : 'Save New'}
            </button>
            <button
              onClick={resetLayout}
              className="layout-action-button layout-reset-button"
              title="Clear the dashboard canvas"
            >
              Blank
            </button>
          </div>

          <div className="saved-layout-list">
            {isLoadingLayouts ? (
              <span className="saved-layout-empty">Loading layouts...</span>
            ) : dashboardConfig.savedLayouts.length === 0 ? (
              <span className="saved-layout-empty">No saved layouts</span>
            ) : (
              dashboardConfig.savedLayouts.map((layout) => (
                <div
                  key={layout.id}
                  className={`saved-layout-chip ${dashboardConfig.activeLayoutId === layout.id ? 'saved-layout-chip-active' : ''}`}
                >
                  <button
                    type="button"
                    className="saved-layout-load"
                    onClick={() => loadLayout(layout)}
                    title={`Load ${layout.name}`}
                  >
                    {layout.name}
                  </button>
                  <button type="button" className="saved-layout-icon-button" onClick={() => renameLayout(layout)} title="Rename">
                    R
                  </button>
                  <button type="button" className="saved-layout-icon-button" onClick={() => duplicateLayout(layout)} title="Duplicate">
                    D
                  </button>
                  <button type="button" className="saved-layout-icon-button saved-layout-delete" onClick={() => deleteLayout(layout)} title="Delete">
                    x
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </header>

      <main className="app-content flex-1 p-4">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
