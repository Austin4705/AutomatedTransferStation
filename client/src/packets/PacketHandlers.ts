import { PacketManager } from './PacketHandler';

// Define interfaces for packet data types
interface CommandData {
  command: string;
  value: number;
}

interface PositionData {
  x: number;
  y: number;
  [key: string]: number | undefined;
}

interface TraceOverResultData {
  message: string;
  success: boolean;
  flakeCount?: number;
}

interface ScanFlakesResultData {
  message: string;
  success: boolean;
  flakeCount?: number;
  directory?: string;
}

// Helper function to refresh a specific camera stream
const createRefreshEvent = (streamType: string, cameraNumber: number) => {
  console.log(`Dispatching refresh event for ${streamType}${cameraNumber}`);
  const event = new CustomEvent('refresh-camera-stream', { 
    detail: { streamType, cameraNumber } 
  });
  window.dispatchEvent(event);
};

// Register packet handlers
export class PacketHandlers {
  @PacketManager.registerHandler("POSITION")
  static handlePosition(data: any) {
    // Ensure we have valid position data
    if (typeof data.x === 'number' && typeof data.y === 'number') {
      console.log("Received valid position data:", data);
    } else {
      console.warn("Received invalid position data:", data);
    }
  }
  
  @PacketManager.registerHandler("RESPONSE_POSITION")
  static handlePositionResponse(data: any) {
    console.log("Received position response data:", data);
    // Position data will be handled by the PositionDisplay component
  }

  @PacketManager.registerHandler("RESPONSE_LOG_COMMANDS")
  static handleCommandLogResponse(data: any) {
    console.log("Received command log data:", data);
    // Command logs will be handled by the CommandLog component
  }

  @PacketManager.registerHandler("RESPONSE_LOG_RESPONSE")
  static handleResponseLogResponse(data: any) {
    console.log("Received response log data:", data);
    // Response logs will be handled by the ResponseLog component
  }

  @PacketManager.registerHandler("COMMAND_RESULT")
  static handleCommandResult(data: any) {
    console.log("Received command result:", data);
    // Command results will be handled by the ResponseLog component
  }

  @PacketManager.registerHandler("TRACE_OVER_RESULT")
  static handleTraceOverResult(data: any) {
    console.log("Received trace over result:", data);
    // Display a notification or update UI based on the result
    if (data.success) {
      // Show success notification
      console.log(`Trace over completed successfully for ${data.flakeCount || 'unknown'} flakes`);
    } else {
      // Show error notification
      console.error(`Trace over failed: ${data.message || 'Unknown error'}`);
    }
  }

  @PacketManager.registerHandler("REFRESH_SNAPSHOT")
  static handleRefreshSnapshot(data: any) {
    console.log("%c Received REFRESH_SNAPSHOT packet:", "background: #3498db; color: white; padding: 4px; border-radius: 4px;", data);
    
    // Extract camera number from the packet
    const cameraNumber = data.camera;
    
    if (typeof cameraNumber === 'number') {
      // Refresh only the snapshot feed for this camera
      console.log(`%c Refreshing snapshot feed for camera ${cameraNumber}`, "background: #2ecc71; color: white; padding: 4px; border-radius: 4px;");
      
      // Dispatch event for snapshot_feed only
      const event = new CustomEvent('refresh-camera-stream', { 
        detail: { streamType: 'snapshot_feed', cameraNumber } 
      });
      window.dispatchEvent(event);
    } else {
      console.warn("%c Invalid camera number in REFRESH_SNAPSHOT packet:", "background: #e74c3c; color: white; padding: 4px; border-radius: 4px;", data);
    }
  }

  @PacketManager.registerHandler("REFRESH_SNAPSHOT_FLAKE_HUNTED")
  static handleRefreshSnapshotFlakeHunted(data: any) {
    console.log("%c Received REFRESH_SNAPSHOT_FLAKE_HUNTED packet:", "background: #9b59b6; color: white; padding: 4px; border-radius: 4px;", data);
    
    // Extract camera number from the packet
    const cameraNumber = data.camera;
    
    if (typeof cameraNumber === 'number') {
      // Refresh only the flake hunted feed for this camera
      console.log(`%c Refreshing flake hunted feed for camera ${cameraNumber}`, "background: #2ecc71; color: white; padding: 4px; border-radius: 4px;");
      
      // Dispatch event for snapshot_flake_hunted only
      const event = new CustomEvent('refresh-camera-stream', { 
        detail: { streamType: 'snapshot_flake_hunted', cameraNumber } 
      });
      window.dispatchEvent(event);
    } else {
      console.warn("%c Invalid camera number in REFRESH_SNAPSHOT_FLAKE_HUNTED packet:", "background: #e74c3c; color: white; padding: 4px; border-radius: 4px;", data);
    }
  }

  @PacketManager.registerHandler("COMMAND")
  static handleCommand(data: any) {
    console.log("Received command:", data);
    // Commands are already handled by the CommandLog component through the jsonState
    // No need to dispatch a custom event as it creates duplicate entries
    
    // Add timestamp if not present to help with log clearing logic
    if (!data.timestamp) {
      data.timestamp = new Date().getTime();
    }
  }

  @PacketManager.registerHandler("RESPONSE")
  static handleResponse(data: any) {
    console.log("Received response:", data);
    // Responses will be handled by the ResponseLog component
  }

  @PacketManager.registerHandler("ERROR")
  static handleError(data: any) {
    console.error("Received error:", data);
    // Errors will be handled by the ResponseLog component
  }

  @PacketManager.registerHandler("RESPONSE_SCAN_FLAKES")
  static handleScanFlakesResult(data: ScanFlakesResultData) {
    console.log("Received scan flakes result:", data);
    
    // Display a notification with the result
    if (data.success) {
      console.log(`Successfully scanned flakes in directory: ${data.directory}`);
      if (data.flakeCount !== undefined) {
        console.log(`Found ${data.flakeCount} flakes`);
      }
    } else {
      console.error(`Failed to scan flakes: ${data.message}`);
    }
  }

  // Default handler for any other packet types
  @PacketManager.registerHandler("DEFAULT")
  static handleDefault(data: any) {
    console.log("Received unhandled packet:", data);
    // Default handling will be done by the appropriate components
  }
} 