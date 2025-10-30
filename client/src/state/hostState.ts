import { atom } from "recoil";

/**
 * State for managing the host/IP address for all connections
 */
export interface HostConfig {
  host: string;
}

export const hostConfigAtom = atom<HostConfig>({
  key: "hostConfig",
  default: {
    host: typeof window !== 'undefined'
      ? (localStorage.getItem('host-config') || '127.0.0.1')
      : '127.0.0.1',
  },
});

