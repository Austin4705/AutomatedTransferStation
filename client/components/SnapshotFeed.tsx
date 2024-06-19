

export default function SnapshotFeed(props: any) {
    const str: string = "http://127.0.0.1:5000/" + props.id;
    return <>
        <img src={str} className="object-scale-down w-full h-full"></img>
    </>
}