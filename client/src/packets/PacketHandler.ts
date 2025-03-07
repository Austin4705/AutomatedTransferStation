import { PacketDefinitions } from './PacketDefinitions';

// Type for packet handler functions
type PacketHandler = (data: any) => void;

export class PacketManager {
  private static handlers: Map<string, PacketHandler> = new Map();
  private static packetDefs: any;

  // Initialize with packet definitions
  static async initialize() {
    try {
      console.log("Loading packet definitions...");
      const response = await fetch('/shared/packet_definitions.json');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      this.packetDefs = await response.json();
      console.log("Successfully loaded packet definitions:", this.packetDefs);
      
      return this.packetDefs;
    } catch (error) {
      console.error('Failed to load packet definitions:', error);
      console.error('Falling back to hardcoded definitions');
      
      // Fallback to hardcoded definitions
      return {};
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