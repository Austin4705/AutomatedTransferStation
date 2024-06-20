import { useEffect } from "react";
import useWebSocket from "react-use-websocket";
import { useSetRecoilState } from "recoil";
import { jsonStateAtom } from "../state/jsonState"

export default function useSocketJSON(ws_url: string) {
  const setJsonState = useSetRecoilState(jsonStateAtom);
  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(
    ws_url,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    { shouldReconnect: (_closeEvent) => true }
  );

  useEffect(() => {
    setJsonState({
      lastJsonMessage: lastJsonMessage,
      readyState: readyState,
      sendJsonMessage: sendJsonMessage
    });
  }, [lastJsonMessage, readyState, sendJsonMessage, setJsonState]);
}
