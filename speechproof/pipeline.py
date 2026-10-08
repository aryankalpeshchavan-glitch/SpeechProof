import json
import sys
from pathlib import Path

from speechproof.asr import transcribe
from speechproof.features import extract
from speechproof.rubric import score
from speechproof.evidence import build_evidence
from db.supabase_db import save_run


def run(wav):
    wav = Path(wav)

    # 1. ASR
    words = transcribe(str(wav))

    # 2. Feature extraction
    features = extract(str(wav), words)

    # 3. Scoring
    result = score(features)

    # 4. Build evidence
    evidence = build_evidence(
        wav,
        features,
        result
    )

    evidence["words"] = words
    evidence["overall_score"] = result["overall_score"]

    # 5. Save everything to Supabase
    run_id = save_run(evidence)

    evidence["run_id"] = run_id

    return evidence


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python -m speechproof.pipeline <audio.wav>")
        sys.exit(1)

    wav = sys.argv[1]

    if not Path(wav).exists():
        print(f"ERROR: Audio file not found: {wav}")
        sys.exit(1)

    result = run(wav)

    print("\nSpeechProof run completed!")
    print(f"Run ID: {result['run_id']}")
    print(f"Overall score: {result['overall_score']}")
    print(f"SHA-256: {result['sha256']}")