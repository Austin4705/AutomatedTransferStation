import { PacketManager } from './PacketHandler';

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

export class PacketHandlers {
  @PacketManager.registerHandler("COMMAND")
  static handleCommand(data: CommandData) {
    console.log(`Executing command: ${data.command} with value: ${data.value}`);
    // Add command handling logic
  }

  @PacketManager.registerHandler("POSITION")
  static handlePosition(data: PositionData) {
    console.log(`Position update - X: ${data.x}, Y: ${data.y}, Z: ${data.z}`);
    // Add position handling logic
  }

  @PacketManager.registerHandler('ERROR')
  static handleError(data: { code: number; message: string }) {
    console.error(`Error ${data.code}: ${data.message}`);
    // Add error handling logic
  }
} 