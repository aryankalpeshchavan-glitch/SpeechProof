
from speechproof.evidence import sha256_json


def test_same_evidence_produces_same_hash():
    evidence = {"run_id": 1, "score": 95.5}

    assert sha256_json(evidence) == sha256_json(evidence)


def test_changed_evidence_produces_different_hash():
    original = {"run_id": 1, "score": 95.5}
    changed = {"run_id": 1, "score": 80.0}

    assert sha256_json(original) != sha256_json(changed)
