import logo from './logo.svg';
import './App.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import Dashboard from './components/dashboard/Dashboard';



// class videoBox extends React.Component{
//   render(){

//     return(
//       <p style={right}>
//         VidBox
//       </p>
//     );
    
//   }
// }
// const right = {
//   float: right,
//   // width: 300px,
//   border: "3px",
//   // padding: "10px"
// };

function clickMe(){
  console.log("clicked");
}

function App() {
  
  return (

    <div className="App">
      {/* Hi this is text */}
      <Dashboard></Dashboard>
      {/* <header className="App-header">
        
        <img src="http://127.0.0.1:5000/video_feed0"></img>
        <videoBox></videoBox>
        <videoBox></videoBox>
        <videoBox></videoBox>
        <button onClick={clickMe}>Default Button Name</button>
        
      </header> */}
    </div>
  );
}

export default App;
