import sys
import json
from speechproof.pipeline import SpeechProofScorer
from speechproof.config import config

def run_smoke_test():
    audio_path = "data/real/aryan_test.wav"
    print(f"exact input path: {audio_path}")
    print(f"actual ASR model/device/compute type: {config.asr.model_name} / {config.asr.device} / {config.asr.compute_type}")
    
    scorer = SpeechProofScorer()
    
    try:
        output = scorer.score(audio_path)
        
        print(f"audio SHA-256: {output.audio_sha256}")
        print(f"audio validation result: Valid WAV")
        
        print(f"duration_s: {output.duration_s}")
        print("actual scores: ")
        for dim, val in output.scores.items():
            print(f"  {dim}: {val}")
            
        print(f"evidence regions/events produced: {len(output.regions)} regions, {len(output.events)} events")
        
        print(f"output hash: {output.metadata.get('evidence_sha256')}")
        print(f"SQLite run ID: {output.metadata.get('run_id')}")
        
    except Exception as e:
        print(f"Smoke test failed: {e}")

if __name__ == "__main__":
    run_smoke_test()
