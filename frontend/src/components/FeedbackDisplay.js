import React from "react";
import "../styles/FeedbackDisplay.css";


const FeedbackDisplay = ({ feedback }) => {
  if (!feedback) return null;

  return (
    <div className="feedback-display">
      <h2>Detailed Feedback</h2>
      <p><strong>Total Reps Done:</strong> {feedback.total_reps_done}</p>
      <p><strong>Problems Detected:</strong> {feedback.problems_detected.join(", ")}</p>
      <h3>Solutions</h3>
      <ul>
        {feedback.solutions.map((solution, index) => (
          <li key={index}>{solution}</li>
        ))}
      </ul>
    </div>
  );
};

export default FeedbackDisplay;
