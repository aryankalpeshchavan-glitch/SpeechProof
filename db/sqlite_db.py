import sqlite3
import os

DB_PATH = "db/ledger.sqlite"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # Initialize schema if not exists
    with open("db/schema.sql") as f:
        conn.executescript(f.read())
        
    return conn

def save_run(evidence):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Save the main run
        cursor.execute(
            """INSERT INTO runs (audio_file, rubric_version, overall_score, sha256) 
               VALUES (?, ?, ?, ?)""",
            (evidence["audio_file"], evidence["rubric_version"], evidence.get("overall_score"), evidence["sha256"])
        )
        run_id = cursor.lastrowid
        
        # 2. Save the five scores
        score_rows = []
        for dimension, score in evidence["scores"].items():
            penalty = evidence.get("penalties", {}).get(dimension, 0)
            score_rows.append((run_id, dimension, score, penalty))
            
        if score_rows:
            cursor.executemany(
                "INSERT INTO scores (run_id, dimension, score, penalty) VALUES (?, ?, ?, ?)",
                score_rows
            )
            
        # 3. Save the measured features
        feature_rows = []
        for name, value in evidence["features"].items():
            if isinstance(value, (int, float)):
                feature_rows.append((run_id, name, value))
                
        if feature_rows:
            cursor.executemany(
                "INSERT INTO features (run_id, feature_name, feature_value) VALUES (?, ?, ?)",
                feature_rows
            )
            
        # 4. Save ASR words and timestamps
        word_rows = []
        for item in evidence.get("words", []):
            word_rows.append((run_id, item["word"], item["start"], item["end"]))
            
        if word_rows:
            cursor.executemany(
                "INSERT INTO words (run_id, word, start, end) VALUES (?, ?, ?, ?)",
                word_rows
            )
            
        conn.commit()
        return run_id
