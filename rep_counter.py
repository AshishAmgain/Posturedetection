import numpy as np

class RepCounter:
    def __init__(self):
        self.count = 0
        self.prev_position = None
        self.going_down = True
        self.threshold_up = 0.4    # More lenient upward threshold
        self.threshold_down = 0.6  # More lenient downward threshold
        self.confidence_threshold = 0.3
        self.min_rep_duration = 10  # Minimum frames between reps
        self.frames_since_last_rep = 0
        
    def update(self, pose):
        """Update rep count based on pushup movement"""
        if not pose or not pose.pose_landmarks:
            return
        
        # Get key landmarks for pushup
        shoulder = pose.pose_landmarks.landmark[11]  # Left shoulder
        elbow = pose.pose_landmarks.landmark[13]    # Left elbow
        wrist = pose.pose_landmarks.landmark[15]    # Left wrist
        
        if not all([lm.visibility > self.confidence_threshold for lm in [shoulder, elbow, wrist]]):
            return
        
        # Calculate pushup position based on elbow angle
        current_position = self.calculate_elbow_angle(shoulder, elbow, wrist) / 180.0
        
        if self.prev_position is not None:
            # Going down
            if self.going_down and current_position < self.threshold_down:
                self.going_down = False
                print(f"Bottom position reached: {current_position:.2f}")
            # Coming up
            elif not self.going_down and current_position > self.threshold_up:
                self.count += 1
                self.going_down = True
                print(f"Pushup rep #{self.count} completed!")
        
        self.prev_position = current_position
    
    def calculate_position(self, hip, knee, ankle):
        """Calculate relative position for rep counting"""
        knee_angle = self.calculate_angle(hip, knee, ankle)
        return knee_angle / 180.0  # Normalize to 0-1 range
    
    def calculate_angle(self, p1, p2, p3):
        """Calculate angle between three points"""
        v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
        
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))
        return np.degrees(angle)
    
    def is_rep_complete(self):
        """Check if a rep was just completed"""
        return not self.going_down 