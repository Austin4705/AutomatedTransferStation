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
  waferCount?: number;
  timestamp?: number;
}

interface ScanFlakesResultData {
  message: string;
  success: boolean;
  waferCount?: number;
  directory?: string;
  timestamp?: number;
}

interface DrawFlakesResultData {
  response: string;
  success?: boolean;
  directory?: string;
  timestamp?: number;
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
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    PacketManager.appendToResponses(`Command result: ${data.message || data.response || JSON.stringify(data)}`, logData);
  }

  @PacketManager.registerHandler("TRACE_OVER_RESULT")
  static handleTraceOverResult(data: TraceOverResultData) {
    console.log("Received trace over result:", data);
    
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    // Create a readable message for the log
    let message = `Trace over ${data.success ? 'completed successfully' : 'failed'}`;
    if (data.message) {
      message += `: ${data.message}`;
    }
    if (data.waferCount !== undefined) {
      message += ` (${data.waferCount} wafers)`;
    }
    
    PacketManager.appendToResponses(message, logData);
    
    // Also display a notification for UI feedback
    if (data.success) {
      console.log(`Trace over completed successfully for ${data.waferCount || 'unknown'} wafers`);
    } else {
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
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    PacketManager.appendToCommands(`Received command: ${data.command}`, logData);
  }

  @PacketManager.registerHandler("RESPONSE")
  static handleResponse(data: any) {
    console.log("Received response:", data);
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    PacketManager.appendToResponses(`Received response: ${data.response}`, logData);
  }

  @PacketManager.registerHandler("ERROR")
  static handleError(data: any) {
    console.error("Received error:", data);
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    PacketManager.appendToResponses(`Error: ${data.message || data.error || JSON.stringify(data)}`, logData);
  }

  @PacketManager.registerHandler("SCAN_FLAKES_RESPONSE")
  static handleScanFlakesResult(data: ScanFlakesResultData) {
    console.log("Received scan flakes result:", data);
    
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    // Create a readable message for the log
    let message = `Scan flakes ${data.success ? 'completed successfully' : 'failed'}`;
    if (data.message) {
      message += `: ${data.message}`;
    }
    if (data.directory) {
      message += ` in directory ${data.directory}`;
    }
    if (data.waferCount !== undefined) {
      message += ` (${data.waferCount} wafers)`;
    }
    
    PacketManager.appendToResponses(message, logData);
    
    // Also display a notification for UI feedback
    if (data.success) {
      console.log(`Successfully scanned flakes in directory: ${data.directory}`);
      if (data.waferCount !== undefined) {
        console.log(`Found ${data.waferCount} wafers`);
      }
    } else {
      console.error(`Failed to scan flakes: ${data.message}`);
    }
  }

  @PacketManager.registerHandler("DRAW_FLAKES_RESPONSE")
  static handleDrawFlakesResult(data: DrawFlakesResultData) {
    console.log("Received draw flakes result:", data);
    
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    // Create a readable message for the log
    let message = `Draw flakes response`;
    if (data.response) {
      message += `: ${data.response}`;
    }
    if (data.directory) {
      message += ` (directory: ${data.directory})`;
    }
    
    PacketManager.appendToResponses(message, logData);
    
    // Also display a notification for UI feedback
    if (data.response) {
      console.log(`Draw flakes response: ${data.response}`);
      if (data.directory) {
        console.log(`Directory: ${data.directory}`);
      }
    }
  }

  // Default handler for any other packet types
  @PacketManager.registerHandler("DEFAULT")
  static handleDefault(data: any) {
    console.log("Received unhandled packet:", data);
    
    // Always create a timestamp if not present
    const timestamp = data.timestamp || new Date().getTime();
    
    // Create a standardized data object for logging
    const logData = {
      ...data,
      timestamp
    };
    
    // Log to the appropriate log based on packet type pattern
    if (data.type && typeof data.type === 'string') {
      const type = data.type.toUpperCase();
      
      // If it looks like a command, log to commands
      if (type.includes('COMMAND') || type.includes('CMD')) {
        PacketManager.appendToCommands(`Unhandled command: ${JSON.stringify(data)}`, logData);
      } 
      // Otherwise log to responses as a default
      else {
        PacketManager.appendToResponses(`Unhandled packet: ${JSON.stringify(data)}`, logData);
      }
    } else {
      // If no type, default to responses
      PacketManager.appendToResponses(`Unhandled packet: ${JSON.stringify(data)}`, logData);
    }
  }
}