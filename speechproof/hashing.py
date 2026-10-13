import hashlib
import json
from typing import Any, Dict

def hash_audio(audio_bytes: bytes) -> str:
    """Returns SHA-256 hash of raw bytes."""
    return hashlib.sha256(audio_bytes).hexdigest()

def canonical_json_dumps(obj: Any) -> str:
    """Returns a deterministic JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def hash_evidence(evidence: Dict[str, Any]) -> str:
    """
    Returns SHA-256 of the evidence JSON.
    Excludes 'output_sha256' field if present.
    """
    evidence_copy = dict(evidence)
    evidence_copy.pop('output_sha256', None)
    canon = canonical_json_dumps(evidence_copy)
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()
