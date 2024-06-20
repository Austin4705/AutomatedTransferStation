import useSendJSON from "../hooks/useSendJSON"

export default function CustomButton(props: any) {
    const str: string = props.message;
    const buttonText = props.buttonText == null ? "Default": props.buttonText;

    const sendJSONData = useSendJSON();
  
    const sendClientData = (message: string) => {
      sendJSONData(message);
    };

    return <>    
        <button className="bg-gray-200 rounded" onClick={() => sendClientData(str)}>{buttonText}</button>
    </>
}