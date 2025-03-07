import { PacketDefinitions } from './PacketDefinitions';

// Type for packet handler functions
type PacketHandler = (data: any) => void;

export class PacketManager {
  private static handlers: Map<string, PacketHandler> = new Map();
  private static packetDefs = {
    "packets": {
      "COMMAND": {
        "fields": {
          "command": "string",
          "value": "float"
        }
      },
      "POSITION": {
        "fields": {
          "x": "float",
          "y": "float",
          "z": "float"
        }
      }
    }
  };

  // Initialize with packet definitions
  static async initialize() {
    try {
      console.log("Initialized with packet definitions:", this.packetDefs);
      return this.packetDefs;
    } catch (error) {
      console.error('Failed to initialize packet system:', error);
      throw error;
    }
  }

  // Decorator-like function to register handlers
  static registerHandler(packetType: string) {
    return function (
      target: any,
      propertyKey: string,
      descriptor: PropertyDescriptor
    ) {
      PacketManager.handlers.set(packetType, descriptor.value);
      return descriptor;
    };
  }

  // Method to handle incoming packets
  static handlePacket(packet: { type: string; data: any }) {
    try {
      const { type, data } = packet;
      
      // Validate packet against definitions
      if (!this.validatePacket(type, data)) {
        throw new Error(`Invalid packet data for type ${type}`);
      }

      // Get handler or use default
      const handler = this.handlers.get(type) || this.defaultHandler;
      handler(data);
    } catch (error) {
      console.error('Error handling packet:', error);
    }
  }

  // Default handler for unregistered packet types
  private static defaultHandler(data: any) {
    console.log('Received unhandled packet:', data);
  }

  // Validate packet data against definitions
  private static validatePacket(type: string, data: any): boolean {
    const packetDef = this.packetDefs?.packets[type];
    if (!packetDef) return false;

    const fields = packetDef.fields;
    for (const [field, expectedType] of Object.entries(fields)) {
      if (!(field in data)) return false;

      const value = data[field];
      switch (expectedType) {
        case 'bool':
          if (typeof value !== 'boolean') return false;
          break;
        case 'int':
        case 'float':
          if (typeof value !== 'number') return false;
          break;
        case 'string':
          if (typeof value !== 'string') return false;
          break;
      }
    }

    return true;
  }
} 