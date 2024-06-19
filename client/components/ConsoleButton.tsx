import { Button } from "@mui/material";

export interface ConsoleButtonProps {
  background?: string;
  handler: () => void;
  children: string;
}

export default function ConsoleButton(props: ConsoleButtonProps) {
  const { handler, background } = props;

  return <Button onClick={handler} sx={{backgroundColor: background ?? "lightgray"}}>{props.children}</Button>;
}
