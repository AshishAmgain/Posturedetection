import React, { useState, useEffect } from 'react';
import './VideoUploadForm.css';

const VideoUploadForm = () => {
  const [username, setUsername] = useState('');
  const [videoFile, setVideoFile] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  useEffect(() => {
    fetchLeaderboard();
  }, [feedback]);

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch('http://localhost:5000/leaderboard');
      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }
      const data = await response.json();
      setLeaderboard(data);
    } catch (err) {
      console.error('Error fetching leaderboard:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('username', username);

    try {
      // First upload the video
      const uploadResponse = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed with status: ${uploadResponse.status}`);
      }

      const data = await uploadResponse.json();
      console.log('Upload successful:', data);

      // Now fetch the feedback data from the feedback file
      const feedbackResponse = await fetch(`http://localhost:5000/feedback/${data.feedback_path}`);
      
      if (!feedbackResponse.ok) {
        throw new Error('Failed to fetch feedback data');
      }

      const feedbackData = await feedbackResponse.json();
      console.log('Feedback data:', feedbackData);
      
      // Process the feedback data
      const processedFeedback = {
        total_reps: feedbackData.total_reps || 0,
        form_score: feedbackData.form_score || 0,
        problems_detected: feedbackData.problems_detected || [
          "Back alignment needs improvement",
          "Not reaching proper depth",
          "Elbow position needs adjustment"
        ],
        recommendations: feedbackData.recommendations || [
          "Keep your body in a straight line",
          "Lower your chest closer to the ground",
          "Keep elbows at 45-degree angle"
        ]
      };
      
      setFeedback(processedFeedback);

    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to process video. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('video/')) {
        setError('Please upload a valid video file');
        return;
      }
      if (file.size > 100 * 1024 * 1024) {
        setError('File size must be less than 100MB');
        return;
      }
      setVideoFile(file);
      setError(null);
    }
  };

  return (
    <div className="upload-container">
      <form onSubmit={handleSubmit} className="upload-form">
        <h2>Upload Your Exercise Video</h2>
        
        <div className="form-group">
          <label htmlFor="username">Your Name</label>
          <input
            type="text"
            id="username"
            name="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your name"
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="workoutVideo">Choose Video</label>
          <input
            type="file"
            id="workoutVideo"
            name="workoutVideo"
            accept="video/*"
            onChange={handleFileChange}
            required
            className="form-input"
          />
          <small className="file-hint">Maximum file size: 100MB</small>
        </div>

        <button 
          type="submit" 
          disabled={isLoading || !videoFile}
          className="submit-button"
        >
          {isLoading ? (
            <span>
              <span className="spinner"></span>
              Uploading...
            </span>
          ) : (
            'Upload Video'
          )}
        </button>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {feedback && (
          <div className="feedback-section">
            <h3>Workout Analysis Results</h3>
            <p>Total Reps: {feedback.total_reps}</p>
            <p>Form Score: {feedback.form_score}/100</p>
            
            {feedback.problems_detected && feedback.problems_detected.length > 0 ? (
              <>
                <h4>Problems Detected:</h4>
                <ul>
                  {feedback.problems_detected.map((problem, index) => (
                    <li key={index}>{problem}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No form issues detected</p>
            )}
            
            {feedback.recommendations && feedback.recommendations.length > 0 ? (
              <>
                <h4>Recommendations:</h4>
                <ul>
                  {feedback.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No specific recommendations</p>
            )}
          </div>
        )}
      </form>

      <div className="leaderboard-container">
        <button 
          className="leaderboard-toggle-button"
          onClick={() => {
            setShowLeaderboard(!showLeaderboard);
            if (!showLeaderboard) {
              fetchLeaderboard();
            }
          }}
        >
          {showLeaderboard ? 'Hide Leaderboard' : 'Show Leaderboard'}
        </button>

        {showLeaderboard && (
          <div className="leaderboard-section">
            <h3>Leaderboard</h3>
            <table className="leaderboard-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Name</th>
                  <th>Reps</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, index) => (
                  <tr key={index} className={entry.username === username ? 'current-user' : ''}>
                    <td>{index + 1}</td>
                    <td>{entry.username}</td>
                    <td>{entry.total_reps}</td>
                    <td>{entry.form_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoUploadForm; 