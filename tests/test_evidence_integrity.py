import pytest
from speechproof.evidence import sha256_json, verify_evidence, build_evidence
import db.sqlite_db
import sqlite3

def test_evidence_verify_unchanged():
    ev = {"a": 1, "b": 2}
    ev["sha256"] = sha256_json(ev)
    assert verify_evidence(ev) is True

def test_evidence_verify_changed():
    ev = {"a": 1, "b": 2}
    ev["sha256"] = sha256_json(ev)
    
    # Tamper with the evidence
    ev["a"] = 3
    assert verify_evidence(ev) is False

def test_evidence_run_id_does_not_invalidate():
    ev = {"a": 1, "b": 2}
    ev["sha256"] = sha256_json(ev)
    
    # Adding run_id should invalidate it normally, unless explicitly excluded.
    # But wait! `verify_evidence` currently only excludes `sha256`. 
    # Let's fix `verify_evidence` to exclude `run_id` as well!
    ev["run_id"] = 999
    assert verify_evidence(ev) is True

def test_sqlite_payload_verifies(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db.sqlite_db.DB_PATH = str(db_path)
    
    # Initialize DB
    with db.sqlite_db.get_connection() as conn:
        pass
        
    ev = {
        "audio_file": "test.wav",
        "audio_sha256": "fakehash",
        "rubric_version": "1.0",
        "overall_score": 0.9,
        "scores": {"pace": 1.0, "pausing": 0.8},
        "penalties": {},
        "features": {"duration": 1.0},
        "words": [],
        "evidence": []
    }
    ev["sha256"] = sha256_json(ev)
    
    run_id = db.sqlite_db.save_run(ev)
    assert db.sqlite_db.verify_saved_run(run_id) is True
