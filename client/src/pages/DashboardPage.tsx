import IndependentCameraBox from '../components/dashboard/IndependentCameraBox';
import SystemLogsBox from '../components/dashboard/SystemLogsBox';
import CommandInputBox from '../components/dashboard/CommandInputBox';
import PacketInputBox from '../components/dashboard/PacketInputBox';
import TraceOverBox from '../components/dashboard/TraceOverBox';
import ScanFlakesBox from '../components/dashboard/ScanFlakesBox';
import ControlPanel from '../components/dashboard/ControlPanel';
import GridstackLayout from '../components/layout/GridstackLayout';
import GridstackWidget from '../components/layout/GridstackWidget';

const DashboardPage = () => {

  return (
    <div className="dashboard-page" style={{ padding: '1rem', minHeight: 'calc(100vh - 80px)' }}>
      <GridstackLayout>
        {/* Camera 1 */}
        <GridstackWidget
          id="camera-1"
          x={0}
          y={0}
          w={6}
          h={6}
          minW={4}
          minH={5}
        >
          <div className="h-full flex flex-col">
            <h2 className="dashboard-box-header bg-gray-50 p-2 rounded-t font-semibold text-gray-800">
              Camera View 1
            </h2>
            <div className="flex-grow overflow-auto">
              <IndependentCameraBox cameraId="camera-1" defaultCamera={0} />
            </div>
          </div>
        </GridstackWidget>

        {/* Camera 2 */}
        <GridstackWidget
          id="camera-2"
          x={6}
          y={0}
          w={6}
          h={6}
          minW={4}
          minH={5}
        >
          <div className="h-full flex flex-col">
            <h2 className="dashboard-box-header bg-gray-50 p-2 rounded-t font-semibold text-gray-800">
              Camera View 2
            </h2>
            <div className="flex-grow overflow-auto">
              <IndependentCameraBox cameraId="camera-2" defaultCamera={1} />
            </div>
          </div>
        </GridstackWidget>

        {/* Trace Over Box */}
        <GridstackWidget
          id="trace-over"
          x={0}
          y={6}
          w={6}
          h={5}
          minW={4}
          minH={4}
        >
          <div className="trace-over-container h-full overflow-auto p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              Trace Over
            </h2>
            <TraceOverBox />
          </div>
        </GridstackWidget>

        {/* Scan Flakes Box */}
        <GridstackWidget
          id="scan-flakes"
          x={6}
          y={6}
          w={6}
          h={5}
          minW={4}
          minH={3}
        >
          <div className="h-full overflow-auto p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              Scan Flakes
            </h2>
            <ScanFlakesBox />
          </div>
        </GridstackWidget>

        {/* Command Input Box */}
        <GridstackWidget
          id="commands"
          x={0}
          y={11}
          w={4}
          h={4}
          minW={3}
          minH={3}
        >
          <div className="h-full overflow-auto p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              Command Input
            </h2>
            <CommandInputBox />
          </div>
        </GridstackWidget>

        {/* Control Panel */}
        <GridstackWidget
          id="control-panel"
          x={4}
          y={11}
          w={4}
          h={6}
          minW={3}
          minH={5}
        >
          <div className="h-full overflow-auto p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              Control Panel
            </h2>
            <ControlPanel />
          </div>
        </GridstackWidget>

        {/* Packet Input Box */}
        <GridstackWidget
          id="packets"
          x={8}
          y={11}
          w={4}
          h={4}
          minW={4}
          minH={3}
        >
          <div className="h-full overflow-auto p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              Packet Input
            </h2>
            <PacketInputBox />
          </div>
        </GridstackWidget>

        {/* System Logs Box */}
        <GridstackWidget
          id="logs"
          x={0}
          y={15}
          w={12}
          h={6}
          minW={6}
          minH={4}
        >
          <div className="log-container h-full flex flex-col p-4">
            <h2 className="dashboard-box-header mb-2 font-semibold text-gray-800">
              System Logs
            </h2>
            <div className="dashboard-log-wrapper flex-1 overflow-hidden">
              <SystemLogsBox />
            </div>
          </div>
        </GridstackWidget>
      </GridstackLayout>
    </div>
  );
}

export default DashboardPage; 