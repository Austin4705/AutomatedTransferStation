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
    host: "127.0.0.1",
  },
});

