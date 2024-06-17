export default function CameraFeed(props: any, ref: any) {
    const str: string = "http://127.0.0.1:5000/video_feed" + props.id;
    // const str2: string = ref.current.scrollHeight + "px";
    return <>
        <iframe src={str} height="480px" width="640px"></iframe>
    </>
}