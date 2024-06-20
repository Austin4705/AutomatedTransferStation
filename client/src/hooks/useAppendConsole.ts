import { useSetRecoilState } from "recoil";
import { consoleStateAtom, consoleMessage } from "../state/consoleState"

export default function useAppendConsole () {
  const setConsoleState = useSetRecoilState(consoleStateAtom);

  const appendData = (line: consoleMessage) =>
    setConsoleState((log) => log.concat([line]));
  return appendData;
}
