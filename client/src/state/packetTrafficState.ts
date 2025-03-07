import { atom } from 'recoil';

export interface PacketTrafficLog {
  timestamp: number;
  type: string;
  data: any;
  size: number; // Approximate size in bytes
  rawData?: string | null; // Raw message string
}

export const packetTrafficLogsAtom = atom<PacketTrafficLog[]>({
  key: "packetTrafficLogs",
  default: [],
});

// Helper function to estimate packet size in bytes
export function estimatePacketSize(packet: any): number {
  try {
    const jsonString = JSON.stringify(packet);
    return new Blob([jsonString]).size;
  } catch (error) {
    return 0;
  }
}

// Helper function to validate if an object is a PacketTrafficLog
export function isPacketTrafficLog(log: PacketTrafficLog | unknown | null): log is PacketTrafficLog {
  return (
    log !== null &&
    (log as PacketTrafficLog).timestamp !== undefined &&
    (log as PacketTrafficLog).type !== undefined &&
    (log as PacketTrafficLog).data !== undefined &&
    (log as PacketTrafficLog).size !== undefined
  );
} 