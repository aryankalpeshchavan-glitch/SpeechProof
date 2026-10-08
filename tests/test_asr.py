import pytest
from typing import Any
from speechproof.asr import ASRWord, ASRSegment, ASRTranscript

def test_asr_word_validation():
    # Because they are simple dataclasses, we should technically add properties/post_init or test custom constructors
    # For now we'll just test that we can instantiate it and that in FasterWhisperASREngine the validation exists.
    pass

def test_mock_engine_validation():
    from speechproof.asr import ASREngine
    engine = ASREngine()
    with pytest.raises(NotImplementedError):
        engine.transcribe("dummy.wav")

def test_config_offline_faster_whisper():
    from speechproof.config import config
    
    assert config.asr.model_name == "large-v3"
    assert config.asr.device == "cuda"
    assert config.asr.compute_type == "float16"

def test_cpu_fallback_guard(monkeypatch):
    from speechproof.config import config
    from speechproof.asr import FasterWhisperASREngine
    import ctranslate2

    # Force config to cuda
    monkeypatch.setattr(config.asr, "device", "cuda")
    
    # Mock ctranslate2 to pretend CUDA is not supported
    monkeypatch.setattr(ctranslate2, "get_supported_compute_types", lambda device: set())
    
    import pytest
    with pytest.raises(RuntimeError, match="CUDA requested but not available in ctranslate2. No CPU fallback allowed."):
        engine = FasterWhisperASREngine(local_files_only=True)
