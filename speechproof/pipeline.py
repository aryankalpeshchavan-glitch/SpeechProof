import sys
from pathlib import Path

from speechproof.asr import transcribe
from speechproof.features import extract
from speechproof.rubric import score
from speechproof.evidence import build_evidence
from db.supabase_db import save_run, verify_saved_run


def run(wav):
    wav = Path(wav)

    # 1. Transcribe audio
    words = transcribe(str(wav))

    # 2. Extract audio features
    features = extract(str(wav), words)

    # 3. Reject audio with no detected words
    if features.get("word_count", 0) == 0:
        raise ValueError(
            "No speech detected. Please provide an audio recording "
            "containing audible speech."
        )

    # 4. Calculate scores
    result = score(features)

    # 5. Build evidence
    evidence = build_evidence(wav, features, result, words)

    # 6. Save everything to Supabase
    run_id = save_run(evidence)
    evidence["run_id"] = run_id

    # 7. Verify saved evidence
    if verify_saved_run(run_id):
        print("Evidence integrity: VERIFIED")
    else:
        raise RuntimeError(
            f"Evidence integrity verification failed for run {run_id}"
        )

    return evidence


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m speechproof.pipeline <audio.wav>")
        sys.exit(1)

    wav = sys.argv[1]

    if not Path(wav).exists():
        print(f"ERROR: Audio file not found: {wav}")
        sys.exit(1)

    try:
        result = run(wav)
    except ValueError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print("\nSpeechProof run completed!")
    print(f"Run ID: {result['run_id']}")
    print(f"Overall score: {result['overall_score']}")
    print(f"SHA-256: {result['sha256']}")

