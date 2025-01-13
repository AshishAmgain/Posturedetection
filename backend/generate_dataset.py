import cv2
import mediapipe as mp
import pandas as pd
import os

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Define dataset directory and output CSV
video_dir = "./datasets/videos"
output_csv = "./datasets/exercise_data.csv"

# Define exercise labels for the dataset
labels = {
    "squat": "squat_video.mp4",
    "pushup": "pushup_video.mp4",
    "bench_press": "bench_press_video.mp4"
}

# Prepare dataset
data = []
for label, video_file in labels.items():
    video_path = os.path.join(video_dir, video_file)
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = [lm.x for lm in results.pose_landmarks.landmark] + \
                        [lm.y for lm in results.pose_landmarks.landmark] + \
                        [lm.z for lm in results.pose_landmarks.landmark]
            data.append(landmarks + [label])

    cap.release()

# Convert to DataFrame
columns = [f"x{i}" for i in range(33)] + [f"y{i}" for i in range(33)] + [f"z{i}" for i in range(33)] + ["label"]
df = pd.DataFrame(data, columns=columns)

try:
    df.to_csv(output_csv, index=False)
    print(f"Dataset saved to {output_csv}")
except PermissionError:
    print(f"Permission error: Could not write to {output_csv}. Ensure the file is not open or locked.")
