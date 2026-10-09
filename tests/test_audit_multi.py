import pytest
import sqlite3
import wave
import os

from sp_platform.audit import CrashTestLab
from contracts.scorer_protocol import ScorerProtocol, ScorerOutput

def create_dummy_wav(path, channels=1, framerate=16000, duration_s=1.0):
    with wave.open(path, 'wb') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b'\x00' * int(framerate * duration_s * 2 * channels))

class DeterministicMockScorer(ScorerProtocol):
    def score(self, audio_path: str) -> ScorerOutput:
        if "fail" in audio_path:
            raise RuntimeError("Intentional failure")
            
        base_name = os.path.basename(audio_path)
        
        # Distinguishable results per recording
        if "1.wav" in base_name:
            scores = {"pace": 10, "energy": 20}
            overall = 15.0
            hash_val = "hash1"
        else:
            scores = {"pace": 90, "pitch": 80}
            overall = 85.0
            hash_val = "hash2"
            
        return ScorerOutput(
            scorer_name="MockScorer",
            scorer_version="1.0",
            scores=scores,
            regions=[],
            events=[],
            quality_flags=[],
            audio_sha256=hash_val,
            duration_s=1.0,
            metadata={"rubric_version": "v1", "overall_score": overall}
        )

def test_audit_multi_recording(tmp_path):
    db_path = tmp_path / "audit_multi.sqlite"
    lab = CrashTestLab(db_path=str(db_path))
    
    wav1 = tmp_path / "test1.wav"
    wav2 = tmp_path / "test2.wav"
    wav_fail = tmp_path / "fail.wav"
    
    create_dummy_wav(str(wav1))
    create_dummy_wav(str(wav2))
    create_dummy_wav(str(wav_fail))
    
    paths = [str(wav1), str(wav_fail), str(wav2)]
    
    lab.run_battery(DeterministicMockScorer(), "multi_test_dataset", paths)
    
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        
        # Expect 2 runs (the failed one is skipped)
        cursor.execute("SELECT run_id, audio_file, sha256, overall_score FROM runs ORDER BY run_id")
        runs = cursor.fetchall()
        assert len(runs) == 2
        
        run1_id, run1_file, run1_hash, run1_score = runs[0]
        run2_id, run2_file, run2_hash, run2_score = runs[1]
        
        assert "test1.wav" in run1_file
        assert run1_hash == "hash1"
        assert run1_score == 15.0
        
        assert "test2.wav" in run2_file
        assert run2_hash == "hash2"
        assert run2_score == 85.0
        
        # Check scores
        cursor.execute("SELECT dimension, score FROM scores WHERE run_id = ? ORDER BY dimension", (run1_id,))
        scores1 = cursor.fetchall()
        assert len(scores1) == 2
        assert scores1[0] == ("energy", 20.0)
        assert scores1[1] == ("pace", 10.0)
        
        cursor.execute("SELECT dimension, score FROM scores WHERE run_id = ? ORDER BY dimension", (run2_id,))
        scores2 = cursor.fetchall()
        assert len(scores2) == 2
        assert scores2[0] == ("pace", 90.0)
        assert scores2[1] == ("pitch", 80.0)
