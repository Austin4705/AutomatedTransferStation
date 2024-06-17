import {SetterOrUpdater, atom} from 'recoil'

export interface consoleMessage {
  message: string;
  sender: string;
  // timestamp: Date;
}

export const consoleState = atom<consoleMessage[]>({
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

export const appendData = (
  line: consoleMessage,
  setLogData: SetterOrUpdater<consoleMessage[]>
) => {
  setLogData((log) => log.concat([line]));
};