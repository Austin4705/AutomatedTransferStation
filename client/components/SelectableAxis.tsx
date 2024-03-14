import { Button } from "@mui/material"

export default function SelectableAxis() {
    const handleClick = (value: number) => {
        // Shit
        console.log("heelo")
    }

    return <>
        <Button variant="contained" onClick={() => handleClick(5)}>+5</Button>
        <Button variant="contained" onClick={() => handleClick(-5)}>-5</Button>
    </>
}