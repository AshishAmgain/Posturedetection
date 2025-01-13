import numpy as np
import mediapipe as mp

class AngleCalculator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        
    def calculate_knee_angle(self, pose):
        """Calculate knee angle"""
        hip = pose.pose_landmarks.landmark[23]  # Left hip
        knee = pose.pose_landmarks.landmark[25]  # Left knee
        ankle = pose.pose_landmarks.landmark[27]  # Left ankle
        return self._calculate_angle(hip, knee, ankle)
    
    def calculate_hip_angle(self, pose):
        """Calculate hip angle"""
        shoulder = pose.pose_landmarks.landmark[11]  # Left shoulder
        hip = pose.pose_landmarks.landmark[23]  # Left hip
        knee = pose.pose_landmarks.landmark[25]  # Left knee
        return self._calculate_angle(shoulder, hip, knee)
    
    def calculate_back_angle(self, pose):
        """Calculate back angle relative to vertical"""
        shoulder = pose.pose_landmarks.landmark[11]  # Left shoulder
        hip = pose.pose_landmarks.landmark[23]  # Left hip
        
        # Create vertical line
        vertical_point = mp.solutions.pose.PoseLandmark()
        vertical_point.x = hip.x
        vertical_point.y = hip.y - 1.0
        vertical_point.z = hip.z
        
        return self._calculate_angle(shoulder, hip, vertical_point)
    
    def calculate_ankle_angle(self, pose):
        """Calculate ankle angle"""
        knee = pose.pose_landmarks.landmark[25]  # Left knee
        ankle = pose.pose_landmarks.landmark[27]  # Left ankle
        toe = pose.pose_landmarks.landmark[31]  # Left toe
        return self._calculate_angle(knee, ankle, toe)
    
    def _calculate_angle(self, p1, p2, p3):
        """Calculate angle between three points"""
        v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
        
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))
        return np.degrees(angle) 