import os
import sys
import json
from speechproof.asr import FasterWhisperASREngine, validate_audio
from speechproof.hashing import canonical_json_dumps

def run_smoke_test(audio_path: str):
    print(f"Running ASR Smoke Test on: {audio_path}")
    validate_audio(audio_path)
    
    engine = FasterWhisperASREngine(local_files_only=True)
    transcript = engine.transcribe(audio_path)
    
    out_dict = {
        "schema_version": "v1-asr-artifact",
        "audio_sha256": transcript.metadata["audio_sha256"],
        "asr": transcript.metadata,
        "segments": [
            {
                "start_s": s.start_s,
                "end_s": s.end_s,
                "text": s.text,
                "words": [
                    {"text": w.word, "start_s": w.start_s, "end_s": w.end_s}
                    for w in s.words
                ]
            }
            for s in transcript.segments
        ]
    }
    
    artifact_path = os.path.join(
        "artifacts", "transcripts", f"{transcript.metadata['audio_sha256']}.json"
    )
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    
    with open(artifact_path, 'w', encoding='utf-8') as f:
        f.write(canonical_json_dumps(out_dict))
        
    print(f"Audio SHA256: {transcript.metadata['audio_sha256']}")
    print(f"Audio duration: {transcript.metadata['duration_s']} s")
    print(f"Model: {transcript.metadata['model_name']}")
    print(f"Device: {engine.cfg.device}")
    print(f"Compute type: {engine.cfg.compute_type}")
    print(f"Language: {transcript.metadata['language']}")
    print(f"Segment count: {transcript.metadata['segment_count']}")
    print(f"Word count: {transcript.metadata['word_count']}")
    
    if transcript.segments and transcript.segments[0].words:
        words = transcript.segments[0].words[:5]
        print("First few timestamped words:")
        for w in words:
            print(f"  [{w.start_s:.2f} - {w.end_s:.2f}] {w.word}")
            
    print(f"\nArtifact saved to: {artifact_path}")
    print("SUCCESS: Smoke test complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <path_to_wav>")
        print("Please place a real 16 kHz mono WAV file in data/real/ and pass its path.")
        sys.exit(1)
    run_smoke_test(sys.argv[1])
