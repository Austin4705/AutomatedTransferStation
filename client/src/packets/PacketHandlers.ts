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

  @PacketManager.registerHandler("COMMAND")
  static handleCommand(data: any) {
    console.log("Received command:", data);
    // Commands will be handled by the CommandLog component
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