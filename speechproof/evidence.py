
import hashlib
import json


def sha256_json(data):
    """Create a repeatable hash of JSON data."""
    canonical = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()

def verify_evidence(evidence):
    """Verify that evidence has not changed since hashing."""
    stored_hash = evidence.get("sha256")

    if not stored_hash:
        return False

    payload = {
        key: value
        for key, value in evidence.items()
        if key not in ("sha256", "run_id")
    }

    return stored_hash == sha256_json(payload)


def build_evidence(audio_file, audio_sha256, features, result, words=None):
    """Build evidence with timestamps for detected long pauses."""

    words = words or []
    events = []

    # Detect gaps between consecutive recognized words.
    for previous, following in zip(words, words[1:]):
        gap = round(following["start"] - previous["end"], 3)

        if gap >= 0.4:
            events.append({
                "dimension": "pausing",
                "type": "long_pause",
                "start": previous["end"],
                "end": following["start"],
                "measured_value": gap,
                "threshold": 0.4,
                "words_before": [previous["word"]],
                "words_after": [following["word"]]
            })

    evidence = {
        "audio_file": str(audio_file),
        "audio_sha256": audio_sha256,
        "rubric_version": result["rubric_version"],
        "scores": result["scores"],
        "penalties": result["penalties"],
        "features": features,
        "evidence": events,
        "words": words,
        "overall_score": result["overall_score"]
    }

    evidence["sha256"] = sha256_json(evidence)

    return evidence