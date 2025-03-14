import { useEffect, useRef } from "react";
import { useRecoilValue } from "recoil";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

import useSocketJSON from "./hooks/useSocketJSON";
import { jsonStateAtom } from "./state/jsonState";
import { PacketManager } from "./packets/PacketHandler";
import { PacketHandlers } from "./packets/PacketHandlers";
import { PositionProvider } from "./state/positionContext";

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
  // Add a ref to track the last processed message
  const lastProcessedMessageRef = useRef<string | null>(null);

  useEffect(() => {
    // Initialize packet system
    console.log("Initializing packet system...");
    PacketManager.initialize().then(() => {
      console.log("Packet system initialized");
      
      // Force the PacketHandlers class to be loaded, which will register all handlers
      // This is necessary because the class uses decorators to register handlers
      // Just referencing the class will cause it to be loaded and the decorators to run
      Object.keys(PacketHandlers).forEach(key => {
        console.log(`Registered handler: ${key}`);
      });
      
      console.log("All packet handlers registered");
    }).catch(error => {
      console.error("Error initializing packet system:", error);
    });
  }, []);

  useEffect(() => {
    if (jsonState.lastJsonMessage && typeof jsonState.lastJsonMessage === 'object' && 'type' in jsonState.lastJsonMessage) {
      const packetType = jsonState.lastJsonMessage.type as string;
      
      // Create a string representation of the message to compare with previously processed messages
      const messageKey = JSON.stringify(jsonState.lastJsonMessage);
      
      // Check if we've already processed this exact message
      if (messageKey === lastProcessedMessageRef.current) {
        // Skip processing if we've already handled this message
        return;
      }
      
      // Update the ref with the current message
      lastProcessedMessageRef.current = messageKey;
      
      // Now log and process the message
      // console.log(`%c Received websocket message of type: ${packetType}`, "background: #f39c12; color: white; padding: 4px; border-radius: 4px;", jsonState.lastJsonMessage);
      
      // Only handle packets if the packet manager is initialized
      if (PacketManager.isKnownPacketType(packetType)) {
        // UNCOMMENT THIS TO SEE THE PACKET TYPE
        // console.log(`%c Handler found for packet type: ${packetType}`, "background: #27ae60; color: white; padding: 4px; border-radius: 4px;");
        
        // Process the packet
        PacketManager.handlePacket(jsonState.lastJsonMessage as any);
      } else {
        console.warn(`%c No handler found for packet type: ${packetType}`, "background: #c0392b; color: white; padding: 4px; border-radius: 4px;");
        console.warn("Initializing packet manager and then handling packet...");
        PacketManager.initialize().then(() => {
          console.log("Packet manager initialized. Now handling delayed packet.");
          PacketManager.handlePacket(jsonState.lastJsonMessage as any);
        });
      }
    }
  }, [jsonState.lastJsonMessage]);

  return (
    <PositionProvider>
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
    </PositionProvider>
  );
}

export default App;
