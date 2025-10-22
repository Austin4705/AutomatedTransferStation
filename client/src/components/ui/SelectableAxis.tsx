// import { Button } from "@mui/material"

export default function SelectableAxis() {
    const handleClick = (value: number) => {
        // Shit
        console.log("heelo")
    }

    return <>
        <button onClick={() => handleClick(5)}>+5</button>
        <button onClick={() => handleClick(-5)}>-5</button>
    </>
}