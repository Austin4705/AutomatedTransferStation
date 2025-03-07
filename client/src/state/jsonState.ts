import { ReadyState } from "react-use-websocket";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";
import { atom } from "recoil";

/**
 * State that is updated to include the latest JSON message, readyState, and a send function
 */
export interface jsonWS {
  lastJsonMessage: unknown;
  lastRawMessage: string | null;
  readyState: ReadyState;
  sendJsonMessage: SendJsonMessage | null;
}

export const jsonStateAtom = atom<jsonWS>({
  key: "jsonState",
  default: {
    lastJsonMessage: null,
    lastRawMessage: null,
    readyState: ReadyState.CLOSED,
    sendJsonMessage: null
  },
});
