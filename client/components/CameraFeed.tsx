import React, { useState } from 'react'

export default function CameraFeed(props: any) {
    const str: string = "http://127.0.0.1:5000/" + props.id;
    // const str2: string = ref.current.scrollHeight + "px";
    // console.log($("#iframe").contents().find("body").html())

    return <>
        <img src={str} className="object-scale-down w-full h-full"></img>
    </>
}