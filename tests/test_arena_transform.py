import pytest
import wave
import os
from fastapi.testclient import TestClient
from contracts.scorer_protocol import ScorerProtocol, ScorerOutput

def create_test_wav(path, channels=1, framerate=16000, duration_s=1.0):
    with wave.open(path, 'wb') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b'\x00' * int(framerate * duration_s * 2 * channels))

class MockScorer(ScorerProtocol):
    def score(self, audio_path: str) -> ScorerOutput:
        # Vary scores based on path/content
        if "out" in audio_path or "cand" in audio_path:
            scores = {"pace": 90.0, "pausing": 60.0, "energy": 85.0, "pitch": 100.0}
            overall = 83.75
        else:
            scores = {"pace": 100.0, "pausing": 95.0, "energy": 90.0, "pitch": 100.0}
            overall = 96.25

        return ScorerOutput(
            scorer_name="MockScorer",
            scorer_version="1.0.0",
            scores=scores,
            regions=[],
            events=[],
            quality_flags=[],
            audio_sha256="mock_hash",
            duration_s=1.0,
            metadata={"overall_score": overall, "rubric_version": "v1"}
        )

@pytest.fixture
def client(monkeypatch):
    import sp_platform.api as api
    monkeypatch.setattr(api, "get_scorer", lambda: MockScorer())
    return TestClient(api.app)

def test_arena_pause_transform(tmp_path, client):
    wav_path = tmp_path / "input.wav"
    create_test_wav(str(wav_path), duration_s=1.0)

    with open(wav_path, "rb") as f:
        resp = client.post(
            "/arena/transform",
            files={"audio": ("input.wav", f, "audio/wav")},
            data={"transform_type": "pause", "intensity": "1.5"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["transform_type"] == "pause"
    assert data["intensity"] == 1.5
    assert data["units"] == "seconds"
    assert data["intended_target"] == "pausing"
    assert data["target_responded"] is True
    assert "audio_data_url" in data
    assert data["audio_data_url"].startswith("data:audio/wav;base64,")
    assert "differences" in data
    assert "pausing" in data["differences"]
    assert data["differences"]["pausing"] == -35.0

def test_arena_pace_transform(tmp_path, client):
    wav_path = tmp_path / "input.wav"
    create_test_wav(str(wav_path), duration_s=1.0)

    with open(wav_path, "rb") as f:
        resp = client.post(
            "/arena/transform",
            files={"audio": ("input.wav", f, "audio/wav")},
            data={"transform_type": "pace", "intensity": "1.2"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["transform_type"] == "pace"
    assert data["intensity"] == 1.2
    assert data["intended_target"] == "pace"
    assert data["target_responded"] is True
    assert "differences" in data

def test_arena_volume_transform(tmp_path, client):
    wav_path = tmp_path / "input.wav"
    create_test_wav(str(wav_path), duration_s=1.0)

    with open(wav_path, "rb") as f:
        resp = client.post(
            "/arena/transform",
            files={"audio": ("input.wav", f, "audio/wav")},
            data={"transform_type": "volume", "intensity": "-3.0"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["transform_type"] == "volume"
    assert data["intensity"] == -3.0
    assert data["intended_target"] == "energy"
    assert data["target_responded"] is True

def test_arena_invalid_intensities(tmp_path, client):
    wav_path = tmp_path / "input.wav"
    create_test_wav(str(wav_path))

    # Pause below min (0.5s)
    with open(wav_path, "rb") as f:
        resp = client.post("/arena/transform", files={"audio": f}, data={"transform_type": "pause", "intensity": "0.1"})
    assert resp.status_code == 400
    assert "out of allowed safety bounds" in resp.json()["detail"]

    # Pace above max (1.5x)
    with open(wav_path, "rb") as f:
        resp = client.post("/arena/transform", files={"audio": f}, data={"transform_type": "pace", "intensity": "2.5"})
    assert resp.status_code == 400
    assert "out of allowed safety bounds" in resp.json()["detail"]

    # Volume out of range
    with open(wav_path, "rb") as f:
        resp = client.post("/arena/transform", files={"audio": f}, data={"transform_type": "volume", "intensity": "20.0"})
    assert resp.status_code == 400
    assert "out of allowed safety bounds" in resp.json()["detail"]

def test_arena_unsupported_type(tmp_path, client):
    wav_path = tmp_path / "input.wav"
    create_test_wav(str(wav_path))
    with open(wav_path, "rb") as f:
        resp = client.post("/arena/transform", files={"audio": f}, data={"transform_type": "teleport", "intensity": "1.0"})
    assert resp.status_code == 400
    assert "Unsupported transform_type" in resp.json()["detail"]

def test_compare_endpoint(tmp_path, client):
    ref_path = tmp_path / "ref.wav"
    cand_path = tmp_path / "cand.wav"
    create_test_wav(str(ref_path))
    create_test_wav(str(cand_path))

    with open(ref_path, "rb") as f_ref, open(cand_path, "rb") as f_cand:
        resp = client.post("/compare", files={"reference": f_ref, "candidate": f_cand})

    assert resp.status_code == 200
    data = resp.json()
    assert "reference" in data
    assert "candidate" in data
    assert "differences" in data
    assert "overall_delta" in data
    assert "limitations" in data

def test_validation_endpoint(client):
    resp = client.get("/validation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "items" in data
    assert len(data["items"]) >= 10
    ids = [item["id"] for item in data["items"]]
    assert "T1" in ids
    assert "T4" in ids
    assert "T6" in ids
    assert "A1-A5" in ids

def test_health_and_ready(client):
    resp_h = client.get("/health")
    assert resp_h.status_code == 200
    assert resp_h.json()["status"] == "ok"

    resp_r = client.get("/ready")
    assert resp_r.status_code == 200
    assert "status" in resp_r.json()
