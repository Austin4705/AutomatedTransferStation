import React from "react";

export interface ConsoleButtonProps {
  background?: string;
  handler: React.MouseEventHandler<HTMLButtonElement>;
  children: string;
}

export default function ConsoleButton(props: ConsoleButtonProps) {
  const { handler, background } = props;

  return <button onClick={handler} style={{backgroundColor: background ?? "lightgray"}}>{props.children}</button>;
}
