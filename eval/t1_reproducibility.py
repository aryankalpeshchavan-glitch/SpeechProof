import json
import time
import subprocess
import hashlib
from typing import List, Dict, Any
from pathlib import Path

from speechproof.pipeline import SpeechProofScorer
from speechproof.config import config

def run_t1():
    audio_path = "data/real/aryan_test.wav"
    print(f"Starting T1 - Reproducibility Evaluation on {audio_path}")
    
    if not Path(audio_path).exists():
        print(f"BLOCKER: Authorized recording {audio_path} is missing.")
        return

    with open(audio_path, 'rb') as f:
        input_audio_sha256 = hashlib.sha256(f.read()).hexdigest()
        
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        git_commit = "unknown"

    metadata = {
        "input_audio_sha256": input_audio_sha256,
        "scorer_version": "1.0.0",
        "rubric_version": "rubric-v0.1",
        "git_commit": git_commit,
        "asr_model": config.asr.model_name,
        "device": config.asr.device,
        "compute_type": config.asr.compute_type,
        "start_time": time.time()
    }
    
    print("Metadata:", metadata)
    
    runs = []
    failed = 0
    scorer = SpeechProofScorer()
    
    for i in range(5):
        print(f"Executing run {i+1}/5...")
        try:
            output = scorer.score(audio_path)
            runs.append(output)
            print(f"Run {i+1} completed successfully.")
        except Exception as e:
            print(f"Run {i+1} failed: {e}")
            failed += 1
            
    if not runs:
        print("All runs failed.")
        return
        
    print("\n--- Reproducibility Checks ---")
    first_run = runs[0]
    
    # 1. Compare dimension scores and overall scores
    scores_match = True
    for r in runs[1:]:
        if r.scores != first_run.scores or r.metadata.get("overall_score") != first_run.metadata.get("overall_score"):
            scores_match = False
            break
            
    # 2. Compare canonical evidence hashes
    hashes_match = True
    for r in runs[1:]:
        if r.metadata.get("evidence_sha256") != first_run.metadata.get("evidence_sha256"):
            hashes_match = False
            break
            
    # 3. Compare evidence regions
    regions_match = True
    for r in runs[1:]:
        if r.regions != first_run.regions:
            regions_match = False
            break

    # 4. Compare word transcripts and timestamps
    words_match = True
    for r in runs[1:]:
        if r.metadata.get("words") != first_run.metadata.get("words"):
            words_match = False
            break
            
    print(f"Dimension & Overall Scores Match: {scores_match}")
    print(f"Word Transcripts & Timestamps Match: {words_match}")
    print(f"Evidence Regions Match: {regions_match}")
    print(f"Canonical Evidence Hashes Match: {hashes_match}")
    
    result = {
        "metadata": metadata,
        "runs_attempted": 5,
        "runs_successful": len(runs),
        "runs_failed": failed,
        "reproducibility": {
            "scores_match": scores_match,
            "words_match": words_match,
            "regions_match": regions_match,
            "evidence_hashes_match": hashes_match
        },
        "cross_machine_test": "NOT RUN (only one machine available)"
    }
    
    with open("eval/t1_results.json", "w") as f:
        json.dump(result, f, indent=2)
        
    print("\nEvaluation complete. Results saved to eval/t1_results.json")

if __name__ == "__main__":
    run_t1()
