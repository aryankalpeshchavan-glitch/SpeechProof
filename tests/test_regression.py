import pytest
import os
import sqlite3
import wave
from fastapi.testclient import TestClient

def create_dummy_wav(path, channels=1, framerate=16000, duration_s=1.0):
    with wave.open(path, 'wb') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b'\x00' * int(framerate * duration_s * 2 * channels))

def test_1_2_supabase_lazy_init(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    
    # 1. Importing doesn't fail
    from db.supabase_db import get_supabase_client
    
    # 2. Fails when called
    with pytest.raises(ValueError, match="Supabase credentials not found"):
        get_supabase_client()

def test_4_audio_validation(tmp_path):
    from speechproof.asr import validate_audio
    
    # Non-wav
    txt_path = tmp_path / "dummy.txt"
    txt_path.write_text("not audio")
    with pytest.raises(ValueError, match="WAV file"):
        validate_audio(str(txt_path))
        
    # Stereo
    stereo_path = tmp_path / "stereo.wav"
    create_dummy_wav(str(stereo_path), channels=2)
    with pytest.raises(ValueError, match="mono"):
        validate_audio(str(stereo_path))
        
    # Bad SR
    bad_sr_path = tmp_path / "badsr.wav"
    create_dummy_wav(str(bad_sr_path), framerate=8000)
    with pytest.raises(ValueError, match="16 kHz"):
        validate_audio(str(bad_sr_path))
        
    # Valid
    valid_path = tmp_path / "valid.wav"
    create_dummy_wav(str(valid_path))
    validate_audio(str(valid_path))

def test_9_sqlite_initialization(tmp_path):
    from db.sqlite_db import get_connection, save_run
    import db.sqlite_db
    
    db_path = tmp_path / "test.sqlite"
    db.sqlite_db.DB_PATH = str(db_path)
    
    evidence = {
        "audio_file": "test.wav",
        "rubric_version": "1.0",
        "overall_score": 0.9,
        "sha256": "fakehash",
        "scores": {"pace": 1.0, "pausing": 0.8},
        "features": {"duration": 1.0},
        "words": []
    }
    
    run_id = save_run(evidence)
    assert run_id == 1
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT dimension, score FROM scores WHERE run_id = 1")
        rows = cursor.fetchall()
        assert len(rows) == 2

def test_10_audit_engine(tmp_path, monkeypatch):
    from sp_platform.audit import CrashTestLab
    from contracts.scorer_protocol import ScorerProtocol, ScorerOutput
    
    db_path = tmp_path / "audit.sqlite"
    lab = CrashTestLab(db_path=str(db_path))
    
    class MockScorer(ScorerProtocol):
        def score(self, audio_path: str) -> ScorerOutput:
            return ScorerOutput(
                scorer_name="TestScorer",
                scorer_version="1.0",
                scores={"pace": 0.5, "fluency": 0.8},
                regions=[],
                events=[],
                quality_flags=[],
                audio_sha256="audhash",
                duration_s=1.0,
                metadata={}
            )
            
    valid_path = tmp_path / "valid.wav"
    create_dummy_wav(str(valid_path))
    
    lab.run_battery(MockScorer(), "test_dataset", [str(valid_path)])
    
    import sqlite3
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT scorer_name FROM runs")
        assert cursor.fetchone()[0] == "TestScorer"
        
        cursor.execute("SELECT dimension FROM scores")
        dims = [r[0] for r in cursor.fetchall()]
        assert set(dims) == {"pace", "fluency"}

def test_11_12_13_api(tmp_path, monkeypatch):
    from sp_platform.api import app
    from sp_platform.audit import CrashTestLab
    import db.sqlite_db
    
    db_path = tmp_path / "api.sqlite"
    db.sqlite_db.DB_PATH = str(db_path)
    
    # Initialize DB for leaderboard
    with db.sqlite_db.get_connection() as conn:
        conn.cursor().execute("INSERT INTO runs (audio_file, rubric_version, sha256, created_at) VALUES ('a', '1', 'hash', '2020')")
        conn.commit()
        
    client = TestClient(app)
    
    # Test 13: Leaderboard
    
    orig_connect = sqlite3.connect
    def mock_connect(path, *args, **kwargs):
        if path == "db/ledger.sqlite":
            path = str(db_path)
        return orig_connect(path, *args, **kwargs)
    monkeypatch.setattr("sqlite3.connect", mock_connect)
    
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert len(resp.json()["leaderboard"]) == 1
    
    # Test 12: Invalid input
    txt_path = tmp_path / "dummy.txt"
    txt_path.write_text("bad")
    with open(txt_path, "rb") as f:
        resp = client.post("/score", files={"audio": f})
    assert resp.status_code == 400
    assert resp.status_code == 400
    
    # Test 11: Valid scorer injection
    from contracts.scorer_protocol import ScorerOutput
    class DummyScorer:
        def score(self, path):
            return ScorerOutput("Dummy", "1", {}, [], [], [], "hash", 1.0, {})
            
    import sp_platform.api
    monkeypatch.setattr(sp_platform.api, "get_scorer", lambda: DummyScorer())
    
    valid_path = tmp_path / "valid.wav"
    create_dummy_wav(str(valid_path))
    with open(valid_path, "rb") as f:
        resp = client.post("/score", files={"audio": f})
    assert resp.status_code == 200
    assert resp.json()["scorer_name"] == "Dummy"
