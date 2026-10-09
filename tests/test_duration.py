import pytest
from speechproof.pipeline import SpeechProofScorer
from contracts.scorer_protocol import ScorerOutput

def test_scorer_output_duration_s(tmp_path, monkeypatch):
    import speechproof.pipeline
    
    def mock_run(audio_path):
        return {
            "rubric_version": "1.0",
            "overall_score": 90.0,
            "sha256": "hash",
            "run_id": 1,
            "scores": {"pace": 100},
            "evidence": [],
            "features": {"duration_sec": 42.5}
        }
    
    monkeypatch.setattr(speechproof.pipeline, "run", mock_run)
    import speechproof.asr
    monkeypatch.setattr(speechproof.asr, "validate_audio", lambda x: None)
    
    # create dummy wav for sha256
    import wave
    dummy_path = tmp_path / "dummy.wav"
    with wave.open(str(dummy_path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b'\x00' * 16000)
        
    scorer = SpeechProofScorer()
    output = scorer.score(str(dummy_path))
    assert output.duration_s == 42.5
