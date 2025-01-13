import cv2
import mediapipe as mp
import numpy as np
import json
import os
import joblib

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
drawing_utils = mp.solutions.drawing_utils

# Load the model
model_path = "./models/exercise_classifier.pkl"
try:
    model = joblib.load(model_path)
    print("Model loaded successfully!")
except FileNotFoundError:
    print(f"Error: Model file not found at {model_path}")
    model = None

# Process video
def process_video(video_path, processed_dir, feedback_dir):
    cap = cv2.VideoCapture(video_path)
    filename = os.path.basename(video_path)
    processed_path = os.path.join(processed_dir, f"processed_{filename}")
    feedback_path = os.path.join(feedback_dir, f"{filename}.json")

    out = cv2.VideoWriter(
        processed_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        int(cap.get(cv2.CAP_PROP_FPS)),
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    )

    feedback = []
    reps = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = [[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark]
            flat_landmarks = [coord for lm in landmarks for coord in lm]

            exercise_type = "unknown"
            if model and len(flat_landmarks) == model.n_features_in_:
                try:
                    exercise_type = model.predict([flat_landmarks])[0]
                except Exception as e:
                    print(f"Prediction error: {e}")

            feedback.append(f"Detected: {exercise_type}")
            reps += 1

        out.write(frame)

    cap.release()
    out.release()

    feedback_summary = {
        "total_reps_done": reps,
        "feedback": feedback,
        "score": reps * 10
    }

    with open(feedback_path, 'w') as f:
        json.dump(feedback_summary, f, indent=4)

    return processed_path, feedback_path
