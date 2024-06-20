import {
    consoleMessage,
    consoleStateAtom,
    isConsoleMessage,
  } from "../state/consoleState";
import { useEffect } from "react";
import { jsonStateAtom } from "../state/jsonState";
import { useRecoilValue } from "recoil";


export const useReceiveJSON = (callback: Function) => {
    const logData = useRecoilValue(consoleStateAtom);
    const jsonState = useRecoilValue(jsonStateAtom);

    useEffect(() => {
        if (isConsoleMessage(jsonState.lastJsonMessage)) {
          callback(jsonState.lastJsonMessage);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, [jsonState.lastJsonMessage]);
};