import { useEffect } from "react";
import { useRecoilValue } from "recoil";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

import useSocketJSON from "./hooks/useSocketJSON";
import { jsonStateAtom } from "./state/jsonState";
import { PacketManager } from "./packets/PacketHandler";

// Layout and Pages
import MainLayout from "./components/MainLayout";
import CameraPage from "./pages/CameraPage";
import TraceOverPage from "./pages/TraceOverPage";
import SystemLogsPage from "./pages/SystemLogsPage";
import CommandsPage from "./pages/CommandsPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  const WS_URL = "ws://127.0.0.1:8765";
  useSocketJSON(WS_URL);
  const jsonState = useRecoilValue(jsonStateAtom);

  useEffect(() => {
    // Initialize packet system
    PacketManager.initialize().then(() => {
      console.log("Packet system initialized");
    });
  }, []);

  useEffect(() => {
    if (jsonState.lastJsonMessage) {
      console.log("Received websocket message:", jsonState.lastJsonMessage);
      PacketManager.handlePacket(jsonState.lastJsonMessage as any);
    }
  }, [jsonState.lastJsonMessage]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="camera" element={<CameraPage />} />
          <Route path="trace-over" element={<TraceOverPage />} />
          <Route path="system-logs" element={<SystemLogsPage />} />
          <Route path="commands" element={<CommandsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
