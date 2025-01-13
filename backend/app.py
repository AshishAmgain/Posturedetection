from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
from pose_utils import process_video

# Initialize Flask app
app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "./static/uploads"
PROCESSED_DIR = "./static/processed"
FEEDBACK_DIR = "./static/feedback"
DB_PATH = "leaderboard.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)

# Initialize database
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            reps INTEGER NOT NULL,
            score INTEGER NOT NULL
        )
        """)

@app.route('/upload', methods=['POST'])
def upload_video():
    file = request.files['video']
    user_name = request.form.get("user_name", "Anonymous")
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)

    processed_path, feedback_path = process_video(filepath, PROCESSED_DIR, FEEDBACK_DIR)

    return jsonify({"processed_path": processed_path, "feedback_path": feedback_path})

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT user_name, reps, score FROM leaderboard ORDER BY score DESC")
        results = [{"user_name": row[0], "reps": row[1], "score": row[2]} for row in cursor.fetchall()]
    return jsonify(results)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
