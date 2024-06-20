import {atom, useSetRecoilState} from 'recoil'

export interface consoleMessage {
  message: string;
  sender: string;
}

export const consoleStateAtom = atom<consoleMessage[]>({
  key: "consoleState",
  default: [],
});

export function isConsoleMessage(msg: consoleMessage | unknown | null): msg is consoleMessage {
  return (
    msg !== null &&
    (msg as consoleMessage).message !== undefined &&
    (msg as consoleMessage).sender !== undefined // &&
    // (msg as consoleMessage).timestamp !== undefined
  );
}