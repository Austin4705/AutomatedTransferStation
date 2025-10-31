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
  private static trafficListeners: PacketTrafficListener[] = [];
  private static commandLogListeners: CommandLogListener[] = [];
  private static responseLogListeners: ResponseLogListener[] = [];
  private static lastRawMessage: string | null = null;

  static async initialize() {
    // No longer loading packet definitions - using decorator-based handlers only
    console.log("PacketManager initialized (decorator-based handlers only)");
    return Promise.resolve({});
  }

  static isInitialized(): boolean {
    return true; // Always initialized since we don't need to load definitions
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

      // Check if we have a registered handler for this packet type
      const handler = this.handlers.get(type);
      if (handler) {
        handler(packet);
      } else {
        this.defaultHandler(packet);
      }
    } catch (error) {
      console.error('Error handling packet:', error);
    }
  }

  private static defaultHandler(data: any) {
    console.log('Received unhandled packet:', data);
  }

  static isKnownPacketType(type: string): boolean {
    // Simply check if we have a registered handler for this type
    return this.handlers.has(type);
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