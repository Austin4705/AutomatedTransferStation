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

// Helper function to refresh a specific camera stream
const createRefreshEvent = (streamType: string, cameraNumber: number) => {
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
    console.log("Received REFRESH_SNAPSHOT packet:", data);
    
    // Extract camera number from the packet
    const cameraNumber = data.camera;
    
    if (typeof cameraNumber === 'number') {
      // Refresh the corresponding video feed
      createRefreshEvent("video_feed", cameraNumber);
      console.log(`Refreshing video feed for camera ${cameraNumber} after snapshot`);
    } else {
      console.warn("Invalid camera number in REFRESH_SNAPSHOT packet:", data);
    }
  }

  @PacketManager.registerHandler("REFRESH_SNAPSHOT_FLAKE_HUNTED")
  static handleRefreshSnapshotFlakeHunted(data: any) {
    console.log("Received REFRESH_SNAPSHOT_FLAKE_HUNTED packet:", data);
    
    // Extract camera number from the packet
    const cameraNumber = data.camera;
    
    if (typeof cameraNumber === 'number') {
      // Refresh the corresponding video feed
      createRefreshEvent("video_feed", cameraNumber);
      console.log(`Refreshing video feed for camera ${cameraNumber} after flake hunted snapshot`);
    } else {
      console.warn("Invalid camera number in REFRESH_SNAPSHOT_FLAKE_HUNTED packet:", data);
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

  // Default handler for any other packet types
  @PacketManager.registerHandler("DEFAULT")
  static handleDefault(data: any) {
    console.log("Received unhandled packet:", data);
    // Default handling will be done by the appropriate components
  }
} 