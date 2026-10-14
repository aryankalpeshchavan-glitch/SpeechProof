import os
import tempfile
import numpy as np
import pytest
import soundfile as sf

from speechproof.audio_io import (
    ingest_audio_file,
    normalized_audio_context,
    AudioIngestionError,
    DEFAULT_MAX_UPLOAD_BYTES,
    CANONICAL_SAMPLE_RATE,
)
from speechproof.asr import validate_audio


def test_ingest_already_compliant_wav(tmp_path):
    # Create 1 second of 16kHz mono audio
    sr = CANONICAL_SAMPLE_RATE
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, sr, endpoint=False)).astype(np.float32)
    src_wav = str(tmp_path / "compliant.wav")
    dst_wav = str(tmp_path / "output.wav")
    sf.write(src_wav, audio, sr, subtype="PCM_16")

    # Ingest
    ingest_audio_file(src_wav, dst_wav)

    assert os.path.exists(dst_wav)
    validate_audio(dst_wav)


def test_ingest_stereo_resampling(tmp_path):
    # Create 1 second of 44.1kHz stereo audio
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    ch1 = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    ch2 = np.sin(2 * np.pi * 880 * t).astype(np.float32)
    stereo = np.column_stack([ch1, ch2])

    src_wav = str(tmp_path / "stereo_44k.wav")
    dst_wav = str(tmp_path / "normalized.wav")
    sf.write(src_wav, stereo, sr)

    ingest_audio_file(src_wav, dst_wav)

    assert os.path.exists(dst_wav)
    validate_audio(dst_wav)
    # Verify metadata with soundfile
    info = sf.info(dst_wav)
    assert info.samplerate == 16000
    assert info.channels == 1
    assert info.subtype == "PCM_16"


def test_ingest_empty_file_rejected(tmp_path):
    empty_file = str(tmp_path / "empty.wav")
    with open(empty_file, "wb") as f:
        pass
    dst_wav = str(tmp_path / "output.wav")

    with pytest.raises(AudioIngestionError, match="empty"):
        ingest_audio_file(empty_file, dst_wav)


def test_ingest_max_size_limit_enforced(tmp_path):
    oversized_file = str(tmp_path / "huge.wav")
    with open(oversized_file, "wb") as f:
        f.write(b"0" * 1024)
    dst_wav = str(tmp_path / "output.wav")

    with pytest.raises(AudioIngestionError, match="exceeds maximum allowed limit"):
        ingest_audio_file(oversized_file, dst_wav, max_size_bytes=512)


def test_normalized_audio_context_cleanup(tmp_path):
    sr = 16000
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, sr // 2, endpoint=False)).astype(np.float32)
    src_wav = str(tmp_path / "temp_input.wav")
    sf.write(src_wav, audio, sr, subtype="PCM_16")

    yielded_norm_path = None
    with normalized_audio_context(src_wav, filename_hint="test.wav", temp_dir=str(tmp_path)) as norm_path:
        yielded_norm_path = norm_path
        assert os.path.exists(norm_path)
        validate_audio(norm_path)

    # After context exits, temporary normalized file should be cleaned up
    assert not os.path.exists(yielded_norm_path)
