from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
import sys
import traceback
import platform

app = Flask(__name__)
CORS(app)

# Configure upload folders
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
FEEDBACK_FOLDER = 'static/feedback'

# Create directories if they don't exist
def ensure_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(directory, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        print(f"Error creating/accessing directory {directory}: {str(e)}")
        raise

# Update directory creation
try:
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, FEEDBACK_FOLDER]:
        ensure_directory(folder)
except Exception as e:
    print(f"Failed to create required directories: {str(e)}")

# Add these constants at the top of your file
LEADERBOARD_FILE = "static/leaderboard.json"

# Create leaderboard file if it doesn't exist
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump([], f)

def save_to_leaderboard(username, exercise_type, total_reps, form_score):
    """Save workout data to leaderboard"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
    except:
        leaderboard = []
    
    # Add new entry
    entry = {
        'username': username,
        'exercise_type': exercise_type,
        'total_reps': total_reps,
        'form_score': form_score,
        'timestamp': datetime.now().isoformat(),
    }
    
    leaderboard.append(entry)
    
    # Save updated leaderboard
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f)

class WorkoutAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.rep_counter = 0
        self.stage = None
        self.counter = 0
        self.form_issues = []
        self.exercise_type = None
        self.consecutive_good_reps = 0  # Track consecutive good form reps
        self.depth_scores = []  # Track depth consistency
        self.symmetry_scores = []  # Track movement symmetry
        self.tempo_scores = []  # Track exercise tempo
        self.last_frame_time = None  # For tempo calculation
        
    def detect_exercise_type(self, landmarks):
        """More accurate exercise type detection"""
        try:
            # Get key landmarks
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            
            # Calculate average heights for more stable measurements
            shoulder_height = (left_shoulder.y + right_shoulder.y) / 2
            hip_height = (left_hip.y + right_hip.y) / 2
            knee_height = (left_knee.y + right_knee.y) / 2
            ankle_height = (left_ankle.y + right_ankle.y) / 2
            
            # Calculate body angles
            torso_angle = abs(self.calculate_angle(
                landmarks[self.mp_pose.PoseLandmark.NOSE.value],
                landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
                landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            ))
            
            # Pushup detection criteria:
            # 1. Body is more horizontal (torso angle close to 0 degrees with ground)
            # 2. Shoulders are roughly level with hips
            # 3. Nose is closer to ground level
            is_pushup = (
                torso_angle < 30 and  # Body is nearly horizontal
                abs(shoulder_height - hip_height) < 0.1 and  # Shoulders and hips at similar height
                nose.y > shoulder_height  # Nose below shoulders
            )
            
            # Squat detection criteria:
            # 1. Body is vertical (torso angle close to 90 degrees)
            # 2. Knees are bent (knee position relative to hip and ankle)
            # 3. Shoulders above hips
            is_squat = (
                torso_angle > 45 and  # Body is more vertical
                shoulder_height < hip_height and  # Shoulders above hips
                knee_height > hip_height and  # Knees below hips
                knee_height > ankle_height  # Knees above ankles
            )
            
            if is_pushup:
                print("Detected: Pushup - Body horizontal, shoulders level with hips")
                return "pushup"
            elif is_squat:
                print("Detected: Squat - Body vertical, knees bent")
                return "squat"
            
            print("Exercise type not clearly detected")
            print(f"Torso angle: {torso_angle}")
            print(f"Shoulder-hip diff: {abs(shoulder_height - hip_height)}")
            print(f"Nose height: {nose.y}")
            print(f"Shoulder height: {shoulder_height}")
            return None
            
        except Exception as e:
            print(f"Error in exercise detection: {str(e)}")
            return None

    def analyze_form(self, frame, landmarks):
        """Analyze form based on exercise type"""
        if self.exercise_type is None:
            self.exercise_type = self.detect_exercise_type(landmarks)
            
        if self.exercise_type == "pushup":
            return self.analyze_pushup(frame, landmarks)
        elif self.exercise_type == "squat":
            return self.analyze_squat(frame, landmarks)
        return frame

    def analyze_pushup(self, frame, landmarks):
        """Enhanced pushup analysis with more specific checks"""
        # Get key landmarks
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Calculate angles for both sides
        left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
        
        # Use average elbow angle for more stable detection
        elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        
        # Calculate back angle
        back_angle = self.calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        )
        
        # Calculate elbow flare
        elbow_flare_angle = self.calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        )
        
        # Check head position
        head_alignment = abs(
            landmarks[self.mp_pose.PoseLandmark.NOSE.value].y -
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        )
        
        # Check shoulder symmetry
        shoulder_symmetry = abs(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y -
            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        )
        
        # Enhanced form checks
        if elbow_flare_angle > 45:
            self.form_issues.append("Elbow flaring - keep elbows closer to body")
        
        if head_alignment > 0.1:
            self.form_issues.append("Head dropping - maintain neutral neck position")
        
        if shoulder_symmetry > 0.05:
            self.form_issues.append("Uneven shoulders - maintain level shoulders throughout movement")
        
        # Enhanced rep counting
        if elbow_angle > 160:  # Arms almost straight
            if self.stage != "up":
                self.stage = "up"
                print("Position: Up")
        elif elbow_angle < 90 and self.stage == "up":  # Arms bent, coming from up position
            self.stage = "down"
            self.counter += 1
            print(f"Rep counted! Total: {self.counter}")
        
        # Calculate movement tempo
        current_time = datetime.now()
        if self.last_frame_time:
            time_diff = (current_time - self.last_frame_time).total_seconds()
            if self.stage == "down":
                tempo_score = 100 - abs(2.5 - time_diff) * 20
                self.tempo_scores.append(max(0, tempo_score))
        self.last_frame_time = current_time
        
        # Track depth consistency
        if self.stage == "down":
            ideal_depth = 90  # degrees
            depth_score = 100 - abs(ideal_depth - elbow_angle) * 2
            self.depth_scores.append(max(0, depth_score))
        
        # Track movement symmetry
        symmetry_score = 100 - abs(left_elbow_angle - right_elbow_angle)
        self.symmetry_scores.append(max(0, symmetry_score))
        
        return frame

    def analyze_squat(self, frame, landmarks):
        """Enhanced squat analysis with more specific checks"""
        # Get key landmarks
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
        right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
        left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Calculate angles for both sides
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
        
        # Use average knee angle for more stable detection
        knee_angle = (left_knee_angle + right_knee_angle) / 2
        
        # Calculate hip angle and back angle
        hip_angle = self.calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
        )
        
        back_angle = abs(90 - self.calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        ))
        
        # Check heel position
        left_heel = landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL.value]
        right_heel = landmarks[self.mp_pose.PoseLandmark.RIGHT_HEEL.value]
        heel_height_diff = abs(left_heel.y - right_heel.y)
        
        # Check hip hinge
        hip_hinge_angle = self.calculate_angle(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
        )
        
        # Check spine alignment
        spine_alignment = abs(
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x -
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x
        )
        
        # Enhanced form checks and rep counting
        if heel_height_diff > 0.05:
            self.form_issues.append("Heels lifting - keep weight on heels")
        
        if hip_hinge_angle < 45:
            self.form_issues.append("Poor hip hinge - initiate movement from hips")
        
        if spine_alignment > 0.1:
            self.form_issues.append("Rounded back - maintain neutral spine")
        
        # Calculate movement tempo
        current_time = datetime.now()
        if self.last_frame_time:
            time_diff = (current_time - self.last_frame_time).total_seconds()
            if self.stage == "down":
                tempo_score = 100 - abs(2.5 - time_diff) * 20
                self.tempo_scores.append(max(0, tempo_score))
        self.last_frame_time = current_time
        
        # Track depth consistency
        if self.stage == "down":
            ideal_depth = 90  # degrees for parallel squat
            depth_score = 100 - abs(ideal_depth - knee_angle) * 2
            self.depth_scores.append(max(0, depth_score))
        
        # Track movement symmetry
        symmetry_score = 100 - abs(left_knee_angle - right_knee_angle)
        self.symmetry_scores.append(max(0, symmetry_score))
        
        return frame

    def check_knee_alignment(self, landmarks):
        """Check if knees are properly aligned during squat"""
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
        left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
        right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Check if knees are caving inward
        left_alignment = abs(left_knee.x - left_ankle.x) < 0.1
        right_alignment = abs(right_knee.x - right_ankle.x) < 0.1
        
        return left_alignment and right_alignment

    def generate_recommendations(self):
        """Enhanced recommendations with more detailed feedback"""
        recommendations = []
        
        if self.exercise_type == "pushup":
            if any("Back sagging" in issue for issue in self.form_issues):
                recommendations.extend([
                    "Engage your core by tightening your abs",
                    "Imagine a straight line from head to heels",
                    "Practice plank position to build core strength"
                ])
            if any("Elbow flaring" in issue for issue in self.form_issues):
                recommendations.extend([
                    "Keep elbows at 45-degree angle to your body",
                    "Think of arrows pointing back towards your feet"
                ])
            if any("head dropping" in issue.lower() for issue in self.form_issues):
                recommendations.extend([
                    "Look at a spot on the ground about 6 inches ahead",
                    "Keep your neck in line with your spine"
                ])
                
        elif self.exercise_type == "squat":
            if any("knee" in issue.lower() for issue in self.form_issues):
                recommendations.extend([
                    "Track knees over toes throughout movement",
                    "Engage glutes to prevent knee cave-in",
                    "Try using a resistance band around knees during practice"
                ])
            if any("heel" in issue.lower() for issue in self.form_issues):
                recommendations.extend([
                    "Push through your heels throughout the movement",
                    "Wiggle toes to ensure weight is on heels",
                    "Consider elevating heels slightly during practice"
                ])
            if any("hip hinge" in issue.lower() for issue in self.form_issues):
                recommendations.extend([
                    "Start movement by pushing hips back",
                    "Think of sitting back into a chair",
                    "Practice hip hinge with dowel against back"
                ])
        
        # Add tempo recommendations
        if self.tempo_scores and sum(self.tempo_scores)/len(self.tempo_scores) < 70:
            recommendations.append("Control movement speed: 2-3 seconds down, 1 second up")
        
        # Add consistency recommendations
        if self.depth_scores and sum(self.depth_scores)/len(self.depth_scores) < 70:
            recommendations.append("Focus on consistent depth for each repetition")
        
        return recommendations or ["Excellent form! Keep up the good work!"]

    def calculate_form_score(self):
        """Enhanced form score calculation with multiple metrics"""
        base_score = 100
        
        # Calculate average scores
        depth_score = sum(self.depth_scores) / len(self.depth_scores) if self.depth_scores else 100
        symmetry_score = sum(self.symmetry_scores) / len(self.symmetry_scores) if self.symmetry_scores else 100
        tempo_score = sum(self.tempo_scores) / len(self.tempo_scores) if self.tempo_scores else 100
        
        # Form deductions
        if self.exercise_type == "pushup":
            deductions = {
                "Back sagging": 15,
                "Going too deep": 10,
                "Not going deep enough": 10,
                "Hands too wide": 8,
                "Hands too narrow": 8,
                "Elbow flaring": 12,
                "Head dropping": 5,
                "Uneven shoulders": 10
            }
        else:  # squat
            deductions = {
                "Not squatting deep enough": 15,
                "Excessive forward lean": 15,
                "Knees caving in": 20,
                "Squatting too deep": 10,
                "Heels lifting": 12,
                "Uneven weight distribution": 10,
                "Poor hip hinge": 8,
                "Rounded back": 12
            }
        
        # Apply deductions
        for issue in self.form_issues:
            for key, value in deductions.items():
                if key.lower() in issue.lower():
                    base_score -= value
        
        # Calculate final score with all metrics
        final_score = (
            base_score * 0.4 +  # Form issues
            depth_score * 0.2 +  # Depth consistency
            symmetry_score * 0.2 +  # Movement symmetry
            tempo_score * 0.2  # Exercise tempo
        )
        
        return max(0, min(100, round(final_score)))

    def calculate_angle(self, a, b, c):
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle > 180.0:
            angle = 360-angle
            
        return angle

# Add this function to check the system's video codec
def get_video_codec():
    system = platform.system()
    if system == "Windows":
        return 'DIVX'  # or 'XVID' as fallback for Windows
    return 'mp4v'  # for other systems

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        username = request.form.get('username', 'anonymous')
        
        if video.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Check file type
        allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}
        if not ('.' in video.filename and video.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type. Please upload a video file.'}), 400

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"{username}_{timestamp}_{video.filename}"
            video_path = os.path.join(UPLOAD_FOLDER, video_filename)
            video.save(video_path)
            
            if not os.path.exists(video_path):
                raise Exception("Failed to save video file")
                
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Failed to open video file with OpenCV")
            
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            if frame_width == 0 or frame_height == 0 or fps == 0:
                raise Exception("Invalid video properties")
            
            # Use appropriate codec based on system
            codec = get_video_codec()
            processed_filename = f"processed_{video_filename}"
            processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
            
            # Try different codecs if the first one fails
            codecs_to_try = ['DIVX', 'XVID', 'mp4v', 'avc1']
            out = None
            
            for codec in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    out = cv2.VideoWriter(processed_path, fourcc, fps, (frame_width, frame_height))
                    if out.isOpened():
                        print(f"Successfully opened video writer with codec: {codec}")
                        break
                except Exception as e:
                    print(f"Failed to create video writer with codec {codec}: {str(e)}")
                    continue
            
            if out is None or not out.isOpened():
                raise Exception("Could not initialize video writer with any codec")
            
            analyzer = WorkoutAnalyzer()
            exercise_type_votes = {"pushup": 0, "squat": 0}
            frame_count = 0
            
            print("Starting video processing...")
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"Processed {frame_count} frames")
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = analyzer.pose.process(frame_rgb)
                
                if results.pose_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        analyzer.mp_pose.POSE_CONNECTIONS
                    )
                    
                    detected_type = analyzer.detect_exercise_type(results.pose_landmarks.landmark)
                    if detected_type:
                        exercise_type_votes[detected_type] = exercise_type_votes.get(detected_type, 0) + 1
                    
                    frame = analyzer.analyze_form(frame, results.pose_landmarks.landmark)
                
                out.write(frame)
            
            print(f"Processed {frame_count} total frames")
            print(f"Exercise type votes: {exercise_type_votes}")
            
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            if exercise_type_votes["pushup"] > exercise_type_votes["squat"]:
                analyzer.exercise_type = "pushup"
            elif exercise_type_votes["squat"] > exercise_type_votes["pushup"]:
                analyzer.exercise_type = "squat"
            else:
                analyzer.exercise_type = "unknown"
            
            print(f"Final exercise type: {analyzer.exercise_type}")
            
            feedback = {
                'exercise_type': analyzer.exercise_type,
                'total_reps': analyzer.counter,
                'form_score': analyzer.calculate_form_score(),
                'problems_detected': list(set(analyzer.form_issues)),
                'recommendations': analyzer.generate_recommendations()
            }
            
            feedback_filename = f"{video_filename}.json"
            feedback_path = os.path.join(FEEDBACK_FOLDER, feedback_filename)
            with open(feedback_path, 'w') as f:
                json.dump(feedback, f)
            
            if analyzer.exercise_type not in ['unknown', None]:
                save_to_leaderboard(
                    username=username,
                    exercise_type=analyzer.exercise_type,
                    total_reps=analyzer.counter,
                    form_score=analyzer.calculate_form_score()
                )
            
            return jsonify({
                'feedback': feedback,
                'feedback_path': feedback_path,
                'processed_path': processed_path
            })
            
        except Exception as e:
            print("Error during video processing:")
            traceback.print_exc()
            
            # Clean up any partial files
            for path in [video_path, processed_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
            
            raise Exception(f"Video processing failed: {str(e)}")
            
    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/feedback/<path:feedback_path>')
def get_feedback(feedback_path):
    try:
        # Clean the path to prevent directory traversal
        safe_path = os.path.normpath(feedback_path)
        
        # Read the feedback JSON file
        with open(safe_path, 'r') as f:
            feedback_data = json.load(f)
            
        return jsonify(feedback_data)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to read feedback data',
            'message': str(e)
        }), 500

@app.route('/processed/<path:filename>')
def get_processed_video(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    exercise_type = request.args.get('exercise_type', None)
    time_period = request.args.get('time_period', 'all')  # all, week, month
    
    try:
        # Ensure leaderboard file exists
        if not os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump([], f)
        
        # Read leaderboard data
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
            
        print(f"Raw leaderboard data: {leaderboard}")  # Debug print
        
        # Filter by exercise type if specified and not 'all'
        if exercise_type and exercise_type != 'all':
            leaderboard = [entry for entry in leaderboard if entry['exercise_type'] == exercise_type]
        
        # Filter by time period
        if time_period != 'all':
            now = datetime.now()
            leaderboard = [
                entry for entry in leaderboard 
                if (now - datetime.fromisoformat(entry['timestamp'])).days <= 
                (7 if time_period == 'week' else 30)
            ]
        
        # Sort by total_reps and form_score
        leaderboard.sort(key=lambda x: (x['total_reps'], x['form_score']), reverse=True)
        
        # Return top 10 entries
        result = leaderboard[:10]
        print(f"Filtered and sorted leaderboard data: {result}")  # Debug print
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting leaderboard: {str(e)}")
        return jsonify({'error': f'Failed to get leaderboard: {str(e)}'}), 500

if __name__ == '__main__':
    # Add test entry if leaderboard is empty
    if not os.path.exists(LEADERBOARD_FILE) or os.path.getsize(LEADERBOARD_FILE) == 0:
        test_entry = {
            'username': 'test_user',
            'exercise_type': 'pushup',
            'total_reps': 10,
            'form_score': 95,
            'timestamp': datetime.now().isoformat()
        }
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump([test_entry], f)
    app.run(debug=True) 