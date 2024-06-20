import { useRecoilValue } from "recoil";
import {jsonStateAtom} from "../state/jsonState"
import useAppendConsole from "./useAppendConsole";
import { consoleMessage } from "../state/consoleState";

export default function useSendJSON() {
  const jsonState = useRecoilValue(jsonStateAtom);
  const appendConsole = useAppendConsole();

  const sendClientData = (message: string) => {
    if (message.length == 0) return;

    // It will almost never be null except the very beginning init moments
    if (jsonState.sendJsonMessage === null) return;

    const msg: consoleMessage = {
      sender: "Client",
      message: message,
    };

    jsonState.sendJsonMessage(msg);
    appendConsole(msg);
  };

  return sendClientData;
}