import {useState, useEffect, useRef } from "react";
import { isConsoleMessage } from "../state/consoleState";
import { jsonStateAtom } from "../state/jsonState";
import { useRecoilValue } from "recoil";

export default function CameraFeed(props: any) {
    const defaultStr: string = "http://127.0.0.1:5000/" + props.id;
    const imgRef = useRef(null);

    const jsonState = useRecoilValue(jsonStateAtom);
    useEffect(() => {
      if(isConsoleMessage(jsonState.lastJsonMessage) && jsonState.lastJsonMessage.message == "snapped" && props.id[0] == "s"){
        imgRef.current.src = defaultStr + "?" + new Date().getTime();
      }
    }, [jsonState.lastJsonMessage]);


    return <>
        <img src={defaultStr} ref={imgRef} className="object-scale-down w-full h-full"></img>
    </>
}