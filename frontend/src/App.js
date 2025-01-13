import React from "react";
import VideoUploadForm from "./components/VideoUploadForm";
import "./styles/App.css";



function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Posture Detection System</h1>
      </header>
      <main>
        <VideoUploadForm />
      </main>
    </div>
  );
}

export default App;
