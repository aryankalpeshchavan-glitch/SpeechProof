import hashlib
import json


def sha256_json(data):
    canonical = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def build_evidence(audio_file, features, result):

    evidence = {
        "audio_file": str(audio_file),
        "rubric_version": result["rubric_version"],
        "scores": result["scores"],
        "penalties": result["penalties"],
        "features": features,
        "evidence": [],
    }

    evidence["sha256"] = sha256_json(evidence)

    return evidence


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python speechproof\\evidence.py <features.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        features = json.load(f)

    print(json.dumps(features, indent=2))
