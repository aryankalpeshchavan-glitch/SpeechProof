from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

@app.get("/health")
def health():
    return {"status": "ok", "message": "SpeechProof API is running."}

@app.post("/score")
def score(audio: UploadFile = File(...)):
    import uuid
    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    temp_path = os.path.join("artifacts", temp_filename)
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

@app.post("/compare")
def compare(reference: UploadFile = File(...), candidate: UploadFile = File(...)):
    import uuid
    ref_filename = f"temp_ref_{uuid.uuid4().hex}.wav"
    cand_filename = f"temp_cand_{uuid.uuid4().hex}.wav"
    ref_path = os.path.join("artifacts", ref_filename)
    cand_path = os.path.join("artifacts", cand_filename)
    os.makedirs("artifacts", exist_ok=True)
    
    try:
        with open(ref_path, "wb") as f:
            shutil.copyfileobj(reference.file, f)
        with open(cand_path, "wb") as f:
            shutil.copyfileobj(candidate.file, f)
            
        validate_audio(ref_path)
        validate_audio(cand_path)
        
        scorer = get_scorer()
        ref_output = scorer.score(ref_path)
        cand_output = scorer.score(cand_path)
        
        # very simple contrastive comparison
        diffs = {}
        for dim in ref_output.scores:
            if dim in cand_output.scores:
                diffs[dim] = round(cand_output.scores[dim] - ref_output.scores[dim], 2)
                
        return {
            "reference": asdict(ref_output),
            "candidate": asdict(cand_output),
            "differences": diffs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(ref_path):
            os.remove(ref_path)
        if os.path.exists(cand_path):
            os.remove(cand_path)

@app.post("/arena/transform")
def transform(
    audio: UploadFile = File(...), 
    transform_type: str = Form(...), 
    intensity: float = Form(default=1.0)
):
    import uuid
    import importlib
    temp_filename = f"temp_in_{uuid.uuid4().hex}.wav"
    out_filename = f"temp_out_{uuid.uuid4().hex}.wav"
    temp_path = os.path.join("artifacts", temp_filename)
    out_path = os.path.join("artifacts", out_filename)
    os.makedirs("artifacts", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
            
        validate_audio(temp_path)
        
        if transform_type == "pause":
            from inject.pause import inject_pauses
            inject_pauses(temp_path, out_path, num_pauses=int(intensity))
        elif transform_type == "pace":
            from inject.pace import stretch
            stretch(temp_path, out_path, rate=intensity)
        elif transform_type == "volume":
            from inject.volume import change_volume
            change_volume(temp_path, out_path, db_change=intensity)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported transform_type: {transform_type}")
            
        scorer = get_scorer()
        orig_output = scorer.score(temp_path)
        transformed_output = scorer.score(out_path)
        
        return {
            "original": asdict(orig_output),
            "transformed": asdict(transformed_output)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(out_path):
            os.remove(out_path)

@app.post("/battery/run")
def run_battery():
    # Execute t1-t9 via subprocess or modules. 
    # Returning a NOT_RUN to honor scientific honesty since not all prereqs are met.
    return {"status": "NOT_RUN", "message": "Pilot evaluations require explicit manual triggering and complete datasets. Not all datasets are available for T4-T9."}

@app.get("/leaderboard")
def leaderboard():
    import sqlite3
    try:
        with sqlite3.connect("db/ledger.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 10")
            runs = [dict(row) for row in cursor.fetchall()]
            return {"leaderboard": runs}
    except Exception as e:
        return {"error": str(e), "leaderboard": []}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
