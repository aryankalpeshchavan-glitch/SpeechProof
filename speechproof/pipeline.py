import sys
from pathlib import Path

from speechproof.asr import transcribe
from speechproof.features import extract
from speechproof.rubric import score
from speechproof.evidence import build_evidence
from db.sqlite_db import save_run, verify_saved_run


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

    import hashlib
    with open(wav, 'rb') as f:
        audio_sha256 = hashlib.sha256(f.read()).hexdigest()

    # 5. Build evidence
    evidence = build_evidence(wav, audio_sha256, features, result, words)

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


from contracts.scorer_protocol import ScorerProtocol, ScorerOutput

class SpeechProofScorer(ScorerProtocol):
    def score(self, audio_path: str) -> ScorerOutput:
        import hashlib
        from speechproof.asr import validate_audio

        validate_audio(audio_path)

        with open(audio_path, 'rb') as f:
            audio_sha256 = hashlib.sha256(f.read()).hexdigest()

        evidence = run(audio_path)

        return ScorerOutput(
            scorer_name="SpeechProof",
            scorer_version="1.0.0",
            scores=evidence.get("scores", {}),
            regions=evidence.get("evidence", []),
            events=[],
            quality_flags=["fluency_unavailable"] if "fluency" not in evidence.get("scores", {}) else [],
            audio_sha256=audio_sha256,
            duration_s=evidence.get("features", {}).get("duration_sec", 0.0),
            metadata={
                "rubric_version": evidence.get("rubric_version"),
                "overall_score": evidence.get("overall_score"),
                "evidence_sha256": evidence.get("sha256"),
                "run_id": evidence.get("run_id")
            }
        )


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
