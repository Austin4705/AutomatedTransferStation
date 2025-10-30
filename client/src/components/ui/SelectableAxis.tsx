
export default function SelectableAxis() {
    const handleClick = (value: number) => {
        console.log("heelo")
    }

    return <>
        <button onClick={() => handleClick(5)}>+5</button>
        <button onClick={() => handleClick(-5)}>-5</button>
    </>
}