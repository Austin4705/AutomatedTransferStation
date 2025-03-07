import { PacketManager } from './PacketHandler';
import useAppendConsole from "../hooks/useAppendConsole";
import { store } from "../state/store";

// Define interfaces for packet data types
interface CommandData {
  command: string;
  value: number;
}

interface PositionData {
  x: number;
  y: number;
  z: number;
}

// Register packet handlers
export class PacketHandlers {
  @PacketManager.registerHandler("RESPONSE_POSITION")
  static handlePositionResponse(data: any) {
    console.log("Received position data:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "System",
      message: `Position updated: ${JSON.stringify(data.position)}`
    });
  }

  @PacketManager.registerHandler("RESPONSE_LOG_COMMANDS")
  static handleCommandLogResponse(data: any) {
    console.log("Received command log data:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "System",
      message: `Received ${data.commands?.length || 0} command log entries`
    });
  }

  @PacketManager.registerHandler("RESPONSE_LOG_RESPONSE")
  static handleResponseLogResponse(data: any) {
    console.log("Received response log data:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "System",
      message: `Received ${data.responses?.length || 0} response log entries`
    });
  }

  @PacketManager.registerHandler("COMMAND_RESULT")
  static handleCommandResult(data: any) {
    console.log("Received command result:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "System",
      message: `Command result: ${data.success ? "Success" : "Failed"} - ${data.message || ""}`
    });
  }

  @PacketManager.registerHandler("ERROR")
  static handleError(data: any) {
    console.error("Received error:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "Error",
      message: data.message || "Unknown error"
    });
  }

  // Default handler for any other packet types
  @PacketManager.registerHandler("DEFAULT")
  static handleDefault(data: any) {
    console.log("Received unhandled packet:", data);
    const appendConsole = store.getState().appendConsole;
    appendConsole({
      sender: "System",
      message: `Received packet: ${JSON.stringify(data)}`
    });
  }
} 