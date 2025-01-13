import React, { useRef } from 'react';
import Webcam from 'react-webcam';

const LiveFeed = () => {
  const webcamRef = useRef(null);

  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    console.log('Captured:', imageSrc);
  };

  return (
    <div>
      <h2>Live Camera Feed</h2>
      <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
      <button onClick={captureImage}>Capture</button>
    </div>
  );
};

export default LiveFeed;
