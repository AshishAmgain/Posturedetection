class ExerciseMetrics:
    def __init__(self):
        self.form_thresholds = {
            'squat': {
                'min_knee_angle': 90,
                'max_hip_angle': 45,
                'min_depth': 0.4  # Relative to height
            },
            'pushup': {
                'min_elbow_angle': 90,
                'max_back_angle': 15,
                'min_depth': 0.3
            }
        }

    def analyze_squat_metrics(self, pose, metrics):
        angles = self.calculate_angles(pose)
        
        # Initialize form_issues if not present
        if 'form_issues' not in metrics:
            metrics['form_issues'] = []
        
        # Depth check
        if angles['knee'] > self.form_thresholds['squat']['min_knee_angle']:
            metrics['form_issues'].append("Insufficient squat depth - try going lower")
            
        # Knee alignment
        if not self.check_knee_alignment(pose):
            metrics['form_issues'].append("Knees caving in - keep them aligned with toes")
            
        # Back angle
        if angles['back'] > 45:
            metrics['form_issues'].append("Excessive forward lean - keep chest up")
            
        # Weight distribution
        if not self.check_weight_distribution(pose):
            metrics['form_issues'].append("Uneven weight distribution - keep weight in heels")
        
        metrics['joint_angles'].append(angles)
        return metrics

    def analyze_pushup_metrics(self, pose, metrics):
        angles = self.calculate_angles(pose)
        
        if 'form_issues' not in metrics:
            metrics['form_issues'] = []
        
        # Elbow angle
        if angles['elbow'] > self.form_thresholds['pushup']['min_elbow_angle']:
            metrics['form_issues'].append("Not reaching proper depth - lower chest closer to ground")
            
        # Back alignment
        if angles['back'] > self.form_thresholds['pushup']['max_back_angle']:
            metrics['form_issues'].append("Back sagging - maintain straight line from head to heels")
            
        # Hand position
        if not self.check_hand_position(pose):
            metrics['form_issues'].append("Hands too wide/narrow - place them shoulder-width apart")
        
        metrics['joint_angles'].append(angles)
        return metrics

    def check_knee_alignment(self, pose):
        """Check if knees are aligned with toes"""
        left_hip = pose.pose_landmarks.landmark[23]
        left_knee = pose.pose_landmarks.landmark[25]
        left_ankle = pose.pose_landmarks.landmark[27]
        
        right_hip = pose.pose_landmarks.landmark[24]
        right_knee = pose.pose_landmarks.landmark[26]
        right_ankle = pose.pose_landmarks.landmark[28]
        
        # Check if knees are caving inward
        left_alignment = abs(left_knee.x - left_ankle.x) < 0.1
        right_alignment = abs(right_knee.x - right_ankle.x) < 0.1
        
        return left_alignment and right_alignment

    def check_weight_distribution(self, pose):
        """Check if weight is properly distributed"""
        left_foot = pose.pose_landmarks.landmark[31]
        right_foot = pose.pose_landmarks.landmark[32]
        
        # Check if feet are roughly at same height
        height_diff = abs(left_foot.y - right_foot.y)
        return height_diff < 0.05

    def check_hand_position(self, pose):
        """Check if hands are properly positioned for pushups"""
        left_shoulder = pose.pose_landmarks.landmark[11]
        right_shoulder = pose.pose_landmarks.landmark[12]
        left_wrist = pose.pose_landmarks.landmark[15]
        right_wrist = pose.pose_landmarks.landmark[16]
        
        # Calculate shoulder width
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        
        # Calculate hand width
        hand_width = abs(left_wrist.x - right_wrist.x)
        
        # Hands should be slightly wider than shoulders
        return 0.9 < (hand_width / shoulder_width) < 1.5 

    def check_form_issues(self, angles, exercise_type):
        """Check for form issues based on joint angles"""
        issues = []
        
        if exercise_type == "squat":
            if angles['knee'] < 100:  # Made more sensitive
                issues.append("Squat depth is too shallow - try going lower")
            if angles['back'] > 30:  # Made more sensitive
                issues.append("Excessive forward lean - keep your chest up")
            if angles['hip'] > 85:  # Made more sensitive
                issues.append("Hip hinge needs improvement - push hips back")
            
        elif exercise_type == "pushup":
            if angles['back'] > 10:  # Made more sensitive
                issues.append("Back is sagging - maintain a straight line")
            if angles['hip'] > 10:  # Made more sensitive
                issues.append("Hips are too high - lower your body")
            
        return issues 