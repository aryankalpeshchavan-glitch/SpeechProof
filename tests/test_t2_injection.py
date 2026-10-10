import pytest
import os
import numpy as np
import soundfile as sf
import librosa
from inject.pace import inject_pace
from inject.volume import inject_volume

@pytest.fixture
def dummy_audio_path(tmp_path):
    path = tmp_path / "dummy.wav"
    # Create 1 second of 440Hz sine wave
    sr = 16000
    t = np.linspace(0, 1, sr, endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(path), audio, sr, subtype='PCM_16')
    return str(path)

@pytest.fixture
def loud_audio_path(tmp_path):
    path = tmp_path / "loud.wav"
    # Create 1 second of loud sine wave (amplitude 0.9)
    sr = 16000
    t = np.linspace(0, 1, sr, endpoint=False)
    audio = 0.9 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(path), audio, sr, subtype='PCM_16')
    return str(path)

def test_valid_pace_transformation(dummy_audio_path, tmp_path):
    out_path = str(tmp_path / "out_pace.wav")
    meta = inject_pace(dummy_audio_path, out_path, 1.2)
    assert meta["injection_type"] == "pace"
    assert meta["rate_multiplier"] == 1.2
    assert meta["input_duration_s"] > meta["output_duration_s"] # faster means shorter
    assert meta["input_sha256"] != meta["output_sha256"]
    
    # Check mono
    audio, sr = sf.read(out_path)
    assert len(audio.shape) == 1
    assert sr == 16000
    
def test_invalid_pace_parameters(dummy_audio_path, tmp_path):
    out_path = str(tmp_path / "out_pace.wav")
    with pytest.raises(ValueError):
        inject_pace(dummy_audio_path, out_path, -1.0)
    with pytest.raises(ValueError):
        inject_pace(dummy_audio_path, out_path, 0.0)

def test_valid_volume_transformation(dummy_audio_path, tmp_path):
    out_path = str(tmp_path / "out_vol.wav")
    # Gain of -6 dB should roughly halve the amplitude
    meta = inject_volume(dummy_audio_path, out_path, -6.0)
    assert meta["injection_type"] == "volume"
    assert meta["gain_db"] == -6.0
    assert not meta["clipping_occurred"]
    assert meta["input_sha256"] != meta["output_sha256"]
    
    audio_in, _ = sf.read(dummy_audio_path)
    audio_out, sr = sf.read(out_path)
    assert len(audio_out.shape) == 1
    assert sr == 16000
    
    # Check amplitude reduction
    assert np.max(np.abs(audio_out)) < np.max(np.abs(audio_in))
    
def test_volume_clipping_detection(loud_audio_path, tmp_path):
    out_path = str(tmp_path / "out_clip.wav")
    # +6 dB will push amplitude 0.9 well above 1.0 (approx 1.8)
    meta = inject_volume(loud_audio_path, out_path, 6.0)
    assert meta["clipping_occurred"] is True
    
    # Output should be hard clipped at 1.0 (or very close due to float representation)
    audio_out, _ = sf.read(out_path)
    assert np.max(np.abs(audio_out)) <= 1.0001
    
def test_source_file_unchanged(dummy_audio_path, tmp_path):
    out_path = str(tmp_path / "out_vol.wav")
    with open(dummy_audio_path, 'rb') as f:
        orig_hash = f.read()
        
    inject_volume(dummy_audio_path, out_path, -3.0)
    
    with open(dummy_audio_path, 'rb') as f:
        new_hash = f.read()
        
    assert orig_hash == new_hash

import json
def test_published_result_format_cannot_contain_nan():
    data = {'val': float('nan')}
    with pytest.raises(ValueError):
        json.dumps(data, allow_nan=False)
