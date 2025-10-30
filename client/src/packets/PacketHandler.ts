import { estimatePacketSize } from '../state/packetTrafficState';

type PacketHandler = (data: any) => void;

type PacketTrafficListener = (packet: { type: string; data: any; timestamp: number; size: number; rawData?: string | null }) => void;

type CommandLogEntry = {
  message: string;
  timestamp: number;
  data?: any;
};

type ResponseLogEntry = {
  message: string;
  timestamp: number;
  data?: any;
};

type CommandLogListener = (entry: CommandLogEntry) => void;
type ResponseLogListener = (entry: ResponseLogEntry) => void;

export class PacketManager {
  private static handlers: Map<string, PacketHandler> = new Map();
  private static packetDefs: any;
  private static trafficListeners: PacketTrafficListener[] = [];
  private static commandLogListeners: CommandLogListener[] = [];
  private static responseLogListeners: ResponseLogListener[] = [];
  private static lastRawMessage: string | null = null;

  static async initialize() {
    try {
      console.log("Loading packet definitions...");
      const response = await fetch('/shared/packet_definitions.json');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      console.log("Response:", response.json);
      this.packetDefs = await response.json();
      console.log("Successfully loaded packet definitions:", this.packetDefs);
      
      return this.packetDefs;
    } catch (error) {
      console.error('Failed to load packet definitions:', error);
      return {};
    }
  }

  static isInitialized(): boolean {
    return this.packetDefs !== undefined;
  }

  static setLastRawMessage(message: string | null) {
    this.lastRawMessage = message;
  }

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

  static handlePacket(packet: any) {
    try {
      const type = packet.type;
      
      const timestamp = Date.now();
      const size = estimatePacketSize(packet);
      
      this.notifyTrafficListeners({ 
        type, 
        data: packet,
        timestamp, 
        size,
        rawData: this.lastRawMessage 
      });
      
      if (!this.validatePacket(type, packet)) {
        throw new Error(`Invalid packet data for type ${type}`);
      }

      const handler = this.handlers.get(type) || this.defaultHandler;
      handler(packet);
    } catch (error) {
      console.error('Error handling packet:', error);
    }
  }

  private static defaultHandler(data: any) {
    console.log('Received unhandled packet:', data);
  }

  private static validatePacket(type: string, packet: any): boolean {
    
    const packetDef = this.packetDefs?.packets[type];
    if (!packetDef) return true;

    const fields = packetDef.fields;
    
    for (const [field, expectedType] of Object.entries(fields)) {
      if (field === 'type') continue;
      if (!(field in packet)) {
        console.warn(`Missing field ${field} in packet of type ${type}`);
        return false;
      }

      const value = packet[field];
      
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

  static isKnownPacketType(type: string): boolean {
    if (this.handlers.has(type)) {
      return true;
    }
    
    if (this.packetDefs?.packets && type in this.packetDefs.packets) {
      return true;
    }
    return false;

  }

  static registerTrafficListener(listener: PacketTrafficListener) {
    this.trafficListeners.push(listener);
    return () => {
      const index = this.trafficListeners.indexOf(listener);
      if (index !== -1) {
        this.trafficListeners.splice(index, 1);
      }
    };
  }

  private static notifyTrafficListeners(packetInfo: { type: string; data: any; timestamp: number; size: number; rawData?: string | null }) {
    for (const listener of this.trafficListeners) {
      listener(packetInfo);
    }
  }

  static registerCommandLogListener(listener: CommandLogListener) {
    this.commandLogListeners.push(listener);
    return () => {
      const index = this.commandLogListeners.indexOf(listener);
      if (index !== -1) {
        this.commandLogListeners.splice(index, 1);
      }
    };
  }

  static registerResponseLogListener(listener: ResponseLogListener) {
    this.responseLogListeners.push(listener);
    return () => {
      const index = this.responseLogListeners.indexOf(listener);
      if (index !== -1) {
        this.responseLogListeners.splice(index, 1);
      }
    };
  }

  static appendToCommands(message: string, data?: any) {
    const entry: CommandLogEntry = {
      message,
      timestamp: Date.now(),
      data
    };
    
    for (const listener of this.commandLogListeners) {
      listener(entry);
    }
    
    console.log(`Command: ${message}`, data ? data : '');
  }

  static appendToResponses(message: string, data?: any) {
    const entry: ResponseLogEntry = {
      message,
      timestamp: Date.now(),
      data
    };
    
    for (const listener of this.responseLogListeners) {
      listener(entry);
    }
    
    console.log(`Response: ${message}`, data ? data : '');
  }
} 