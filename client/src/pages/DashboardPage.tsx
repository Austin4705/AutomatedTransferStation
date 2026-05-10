import IndependentCameraBox from '../components/dashboard/IndependentCameraBox';
import SystemLogsBox from '../components/dashboard/SystemLogsBox';
import CommandInputBox from '../components/dashboard/CommandInputBox';
import PacketInputBox from '../components/dashboard/PacketInputBox';
import TraceOverBox from '../components/dashboard/TraceOverBox';
import TraceOverAreaBox from '../components/dashboard/TraceOverAreaBox';
import ScanFlakesBox from '../components/dashboard/ScanFlakesBox';
import GotoFlakeBox from '../components/dashboard/GotoFlakeBox';
import ControlPanel from '../components/dashboard/ControlPanel';
import GridstackLayout from '../components/layout/GridstackLayout';
import GridstackWidget from '../components/layout/GridstackWidget';
import { useRecoilState } from 'recoil';
import { DEFAULT_DASHBOARD_LAYOUT, GridLayoutItem, gridLayoutAtom } from '../state/gridLayoutState';

interface DashboardWidgetDefinition {
  type: string;
  title: string;
  defaultLayout: GridLayoutItem;
  minW: number;
  minH: number;
  render: (layoutItem: GridLayoutItem) => JSX.Element;
}

const widgetDefinitions: DashboardWidgetDefinition[] = [
  {
    type: 'camera',
    title: 'Camera',
    defaultLayout: { id: 'camera', type: 'camera', x: 0, y: 0, w: 6, h: 6 },
    minW: 4,
    minH: 5,
    render: (layoutItem) => <IndependentCameraBox cameraId={layoutItem.id} defaultCamera={0} />,
  },
  {
    type: 'trace-over',
    title: 'Trace Over',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'trace-over')!,
    minW: 4,
    minH: 4,
    render: () => <TraceOverBox />,
  },
  {
    type: 'scan-flakes',
    title: 'Scan Flakes',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'scan-flakes')!,
    minW: 4,
    minH: 3,
    render: () => <ScanFlakesBox />,
  },
  {
    type: 'goto-flake',
    title: 'Go to Flake',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'goto-flake')!,
    minW: 3,
    minH: 3,
    render: () => <GotoFlakeBox />,
  },
  {
    type: 'commands',
    title: 'Command Input',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'commands')!,
    minW: 3,
    minH: 3,
    render: () => <CommandInputBox />,
  },
  {
    type: 'control-panel',
    title: 'Control Panel',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'control-panel')!,
    minW: 3,
    minH: 5,
    render: () => <ControlPanel />,
  },
  {
    type: 'trace-over-area',
    title: 'Trace Over Area',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'trace-over-area')!,
    minW: 4,
    minH: 4,
    render: () => <TraceOverAreaBox />,
  },
  {
    type: 'packets',
    title: 'Packet Input',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'packets')!,
    minW: 4,
    minH: 3,
    render: () => <PacketInputBox />,
  },
  {
    type: 'logs',
    title: 'System Logs',
    defaultLayout: DEFAULT_DASHBOARD_LAYOUT.find((item) => item.id === 'logs')!,
    minW: 6,
    minH: 4,
    render: () => <SystemLogsBox />,
  },
];

const widgetDefinitionByType = new Map(widgetDefinitions.map((definition) => [definition.type, definition]));

const getNextY = (layout: GridLayoutItem[]) =>
  layout.reduce((nextY, item) => Math.max(nextY, item.y + item.h), 0);

const DashboardPage = () => {
  const [gridLayout, setGridLayout] = useRecoilState(gridLayoutAtom);

  const addWidget = (widgetType: string, position?: { x: number; y: number }) => {
    const definition = widgetDefinitionByType.get(widgetType);
    if (!definition) {
      return;
    }

    const defaultLayout = definition.defaultLayout;
    const x = position ? Math.min(position.x, Math.max(0, 12 - defaultLayout.w)) : defaultLayout.x;
    const id = `${widgetType}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    setGridLayout((currentLayout) => {
      const y = position ? position.y : getNextY(currentLayout);
      return [
        ...currentLayout,
        {
          ...defaultLayout,
          id,
          type: widgetType,
          x,
          y,
        },
      ];
    });
  };

  const removeWidget = (widgetId: string) => {
    setGridLayout((currentLayout) => currentLayout.filter((item) => item.id !== widgetId));
  };

  const handlePaletteDragStart = (event: React.DragEvent<HTMLButtonElement>, widgetType: string) => {
    event.dataTransfer.setData('application/x-dashboard-widget', widgetType);
    event.dataTransfer.effectAllowed = 'copy';
  };

  const renderWidgetContent = (definition: DashboardWidgetDefinition, layoutItem: GridLayoutItem) => {
    const isCamera = definition.type === 'camera';
    const isLog = definition.type === 'logs';
    const isTrace = definition.type === 'trace-over' || definition.type === 'trace-over-area';
    const bodyClassName = isCamera
      ? 'flex-grow overflow-auto'
      : isLog
        ? 'dashboard-log-wrapper flex-1 overflow-hidden'
        : 'flex-1 overflow-auto';

    return (
      <div className={`${isLog ? 'log-container' : isTrace ? 'trace-over-container' : ''} h-full flex flex-col`}>
        <div className="dashboard-box-header flex items-center justify-between gap-2 bg-gray-50 p-2 rounded-t font-semibold text-gray-800">
          <span className="truncate">{definition.title}</span>
          <button
            type="button"
            onMouseDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              removeWidget(layoutItem.id);
            }}
            className="dashboard-widget-remove"
            title={`Remove ${definition.title}`}
          >
            x
          </button>
        </div>
        <div className={`${bodyClassName} ${isCamera ? '' : 'p-4 pt-3'}`}>
          {definition.render(layoutItem)}
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-page" style={{ padding: '1rem', minHeight: 'calc(100vh - 80px)' }}>
      <div className="dashboard-layout-toolbar">
        <div className="dashboard-layout-toolbar-text">
          <span className="font-semibold text-gray-800">Components</span>
          <span className="text-xs text-gray-500">Available panels</span>
        </div>
        <div className="dashboard-widget-palette">
          {widgetDefinitions.map((definition) => (
            <button
              key={definition.type}
              type="button"
              draggable
              onDragStart={(event) => handlePaletteDragStart(event, definition.type)}
              onClick={() => addWidget(definition.type)}
              className="dashboard-widget-palette-item"
              title={`Add ${definition.title}`}
            >
              {definition.title}
            </button>
          ))}
        </div>
      </div>

      <GridstackLayout onPaletteDrop={addWidget}>
        {gridLayout.map((layoutItem) => {
          const definition = widgetDefinitionByType.get(layoutItem.type || layoutItem.id);
          if (!definition) {
            return null;
          }

          return (
            <GridstackWidget
              key={layoutItem.id}
              id={layoutItem.id}
              x={layoutItem.x}
              y={layoutItem.y}
              w={layoutItem.w}
              h={layoutItem.h}
              minW={definition.minW}
              minH={definition.minH}
            >
              {renderWidgetContent(definition, layoutItem)}
            </GridstackWidget>
          );
        })}
      </GridstackLayout>
    </div>
  );
}

export default DashboardPage; 
