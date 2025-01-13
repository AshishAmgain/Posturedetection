import React, { useState } from "react";
import axios from "axios";
import "../styles/VideoUpload.css";

const VideoUpload = () => {
  const [file, setFile] = useState(null);
  const [userName, setUserName] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }

    setIsLoading(true);
    setStatusMessage("Uploading video...");

    const formData = new FormData();
    formData.append("video", file);
    formData.append("user_name", userName);

    try {
      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setFeedback(response.data);
      setStatusMessage("Video uploaded successfully! Processing complete.");
    } catch (error) {
      setStatusMessage("Error uploading video. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      setIsLoading(true);
      setStatusMessage("Fetching leaderboard...");
      const response = await axios.get("http://localhost:5000/leaderboard");
      setLeaderboard(response.data);
      setStatusMessage("");
    } catch (error) {
      setStatusMessage("Error fetching leaderboard.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="video-upload">
      <h2>Upload Your Exercise Video</h2>
      <div className="input-group">
        <input
          className="input-field"
          type="text"
          placeholder="Enter your name"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
        />
        <input
          className="file-input"
          type="file"
          accept="video/*"
          onChange={handleFileChange}
        />
      </div>

      <button
        className="upload-button"
        onClick={handleUpload}
        disabled={isLoading}
      >
        Upload Video
      </button>

      {isLoading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      )}

      {statusMessage && <p className="status-message">{statusMessage}</p>}

      {feedback && (
        <div className="feedback-summary">
          <h3>Feedback Summary</h3>
          <p>Total Reps Done: {feedback.total_reps_done || 0}</p>
          <p>Score: {feedback.score || 0}</p>
          <p>
  Problems Detected:{" "}
  {feedback && feedback.problems_detected && feedback.problems_detected.length > 0
    ? feedback.problems_detected.join(", ")
    : "None"}
</p>
<p>Solutions:</p>
<ul>
  {feedback && feedback.solutions && feedback.solutions.length > 0
    ? feedback.solutions.map((solution, index) => (
        <li key={index}>{solution}</li>
      ))
    : <li>No issues detected.</li>}
</ul>

        </div>
      )}

      <button
        className="leaderboard-button"
        onClick={fetchLeaderboard}
        disabled={isLoading}
      >
        Show Leaderboard
      </button>

      {leaderboard.length > 0 && (
        <div className="leaderboard">
          <h3>Leaderboard</h3>
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Reps</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, index) => (
                <tr key={index}>
                  <td>{entry.user_name}</td>
                  <td>{entry.reps}</td>
                  <td>{entry.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default VideoUpload;
