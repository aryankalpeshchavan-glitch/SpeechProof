from fastapi import FastAPI, HTTPException, UploadFile, File
import shutil
import os
from speechproof.asr import validate_audio
from speechproof.pipeline import SpeechProofScorer
from dataclasses import asdict

app = FastAPI()
scorer_instance = None

def get_scorer():
    global scorer_instance
    if scorer_instance is None:
        scorer_instance = SpeechProofScorer()
    return scorer_instance

@app.post("/score")
def score(audio: UploadFile = File(...)):
    temp_path = f"artifacts/temp_{audio.filename}"
    os.makedirs("artifacts", exist_ok=True)
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
            
        validate_audio(temp_path)
        scorer = get_scorer()
        output = scorer.score(temp_path)
        
        return asdict(output)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/battery/run")
def run_battery():
    raise HTTPException(status_code=501, detail="Run battery triggered via API is not fully implemented yet.")

@app.get("/leaderboard")
def leaderboard():
    import sqlite3
    try:
        with sqlite3.connect("db/ledger.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Basic dummy query for frontend, just returning runs
            cursor.execute("SELECT * FROM runs ORDER BY timestamp DESC LIMIT 10")
            runs = [dict(row) for row in cursor.fetchall()]
            return {"leaderboard": runs}
    except Exception as e:
        return {"error": str(e), "leaderboard": []}

@app.post("/arena/transform")
def transform():
    raise HTTPException(status_code=501, detail="Not implemented")
