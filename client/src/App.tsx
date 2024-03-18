import {RecoilRoot} from "recoil";
import MachineLog from "../components/Console";
import CameraFeed from "../components/CameraFeed";

import "./App.css";

function App() {
  return (
    <>
    <RecoilRoot>
      <MachineLog />
      <CameraFeed />
    </RecoilRoot>
    </>
  );
}

export default App;
