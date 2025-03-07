import { estimatePacketSize } from '../state/packetTrafficState';

// Type for packet handler functions
type PacketHandler = (data: any) => void;

// Event system for packet traffic logging
type PacketTrafficListener = (packet: { type: string; data: any; timestamp: number; size: number; rawData?: string | null }) => void;

export class PacketManager {
  private static handlers: Map<string, PacketHandler> = new Map();
  private static packetDefs: any;
  private static trafficListeners: PacketTrafficListener[] = [];
  private static lastRawMessage: string | null = null;

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

  // Set the last raw message
  static setLastRawMessage(message: string | null) {
    this.lastRawMessage = message;
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
  static handlePacket(packet: any) {
    try {
      // Extract the type from the packet
      const type = packet.type;
      
      // Create traffic log entry
      const timestamp = Date.now();
      const size = estimatePacketSize(packet);
      
      // Log packet traffic with the complete packet data
      this.notifyTrafficListeners({ 
        type, 
        data: packet, // Use the complete packet as data
        timestamp, 
        size,
        rawData: this.lastRawMessage 
      });
      
      // Validate packet against definitions
      if (!this.validatePacket(type, packet)) {
        throw new Error(`Invalid packet data for type ${type}`);
      }

      // Get handler or use default
      const handler = this.handlers.get(type) || this.defaultHandler;
      handler(packet);
    } catch (error) {
      console.error('Error handling packet:', error);
    }
  }

  // Default handler for unregistered packet types
  private static defaultHandler(data: any) {
    console.log('Received unhandled packet:', data);
  }

  // Validate packet data against definitions
  private static validatePacket(type: string, packet: any): boolean {
    // Special case for POSITION packets
    if (type === "POSITION") {
      // Only validate that x and y are numbers
      return typeof packet.x === 'number' && typeof packet.y === 'number';
    }
    
    const packetDef = this.packetDefs?.packets[type];
    if (!packetDef) return true; // If no definition exists, consider it valid

    const fields = packetDef.fields;
    
    // Check if required fields exist and have the correct type
    for (const [field, expectedType] of Object.entries(fields)) {
      // Skip type field as it's already validated
      if (field === 'type') continue;
      
      // Check if the field exists in the packet
      if (!(field in packet)) {
        console.warn(`Missing field ${field} in packet of type ${type}`);
        return false;
      }

      const value = packet[field];
      
      // Validate the field type
      switch (expectedType) {
        case 'bool':
          if (typeof value !== 'boolean') {
            console.warn(`Field ${field} should be boolean but got ${typeof value}`);
            return false;
          }
          break;
        case 'int':
          if (typeof value !== 'number' || !Number.isInteger(value)) {
            console.warn(`Field ${field} should be integer but got ${typeof value}`);
            return false;
          }
          break;
        case 'float':
          if (typeof value !== 'number') {
            console.warn(`Field ${field} should be number but got ${typeof value}`);
            return false;
          }
          break;
        case 'string':
          if (typeof value !== 'string') {
            console.warn(`Field ${field} should be string but got ${typeof value}`);
            return false;
          }
          break;
      }
    }

    return true;
  }

  // Check if a packet type is known based on packet definitions
  static isKnownPacketType(type: string): boolean {
    // If we have a registered handler for this type, it's known
    if (this.handlers.has(type)) {
      return true;
    }
    
    // If it's in our packet definitions, it's known
    if (this.packetDefs?.packets && type in this.packetDefs.packets) {
      return true;
    }
    
    // Special case for common packet types that might not be in definitions
    const knownTypes = [];
    
    return knownTypes.includes(type);
  }

  // Register a listener for packet traffic
  static registerTrafficListener(listener: PacketTrafficListener) {
    this.trafficListeners.push(listener);
    return () => {
      // Return unsubscribe function
      const index = this.trafficListeners.indexOf(listener);
      if (index !== -1) {
        this.trafficListeners.splice(index, 1);
      }
    };
  }

  // Notify all traffic listeners
  private static notifyTrafficListeners(packetInfo: { type: string; data: any; timestamp: number; size: number; rawData?: string | null }) {
    for (const listener of this.trafficListeners) {
      listener(packetInfo);
    }
  }
} 