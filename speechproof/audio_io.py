"""
Audio Ingestion and Normalization Module for SpeechProof.

Converts arbitrary user-supplied recordings (WAV, MP3, M4A, AAC, FLAC, OGG,
WebM, MP4) into canonical 16 kHz mono 16-bit PCM WAV audio for deterministic
ASR and acoustic feature extraction.
"""

import os
import shutil
import uuid
import contextlib
from typing import Generator, Optional, BinaryIO
import numpy as np

from speechproof.asr import validate_audio

DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
CANONICAL_SAMPLE_RATE = 16000
SUPPORTED_CONTAINERS = (
    "WAV", "MP3", "M4A", "AAC", "FLAC", "OGG", "WebM", "MP4", "OPUS"
)


class AudioIngestionError(ValueError):
    """Raised when an uploaded audio file fails ingestion, decoding, or validation."""
    pass


def decode_with_pyav(source_path: str, target_wav_path: str) -> None:
    """
    Decodes arbitrary media containers and audio streams (including M4A, AAC, WebM, MP4)
    using PyAV (bundled libav/ffmpeg) and resamples to 16 kHz mono 16-bit PCM WAV.
    """
    import av
    import soundfile as sf

    try:
        container = av.open(source_path)
    except Exception as e:
        raise AudioIngestionError(f"Unable to parse media container: {e}")

    try:
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if not audio_stream:
            raise AudioIngestionError("No valid audio stream detected in uploaded file.")

        resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=CANONICAL_SAMPLE_RATE
        )

        pcm_chunks = []
        for packet in container.demux(audio_stream):
            for frame in packet.decode():
                resampled = resampler.resample(frame)
                if resampled:
                    for rf in resampled:
                        pcm_chunks.append(rf.to_ndarray().flatten())

        flushed = resampler.resample(None)
        if flushed:
            for rf in flushed:
                pcm_chunks.append(rf.to_ndarray().flatten())
    finally:
        container.close()

    if not pcm_chunks:
        raise AudioIngestionError("Decoded audio stream contains zero audio samples.")

    audio_array = np.concatenate(pcm_chunks)
    if len(audio_array) == 0:
        raise AudioIngestionError("Decoded audio duration is 0 seconds.")

    sf.write(target_wav_path, audio_array, CANONICAL_SAMPLE_RATE, subtype="PCM_16")


def decode_with_librosa_or_soundfile(source_path: str, target_wav_path: str) -> bool:
    """
    Attempts decoding standard audio formats (WAV, MP3, FLAC, OGG) via librosa/soundfile.
    Returns True on success, False if format is unhandled or fails.
    """
    try:
        import librosa
        import soundfile as sf

        y, sr = librosa.load(source_path, sr=CANONICAL_SAMPLE_RATE, mono=True)
        if len(y) == 0:
            raise AudioIngestionError("Audio contains zero samples.")
        sf.write(target_wav_path, y, CANONICAL_SAMPLE_RATE, subtype="PCM_16")
        return True
    except Exception:
        return False


def ingest_audio_file(
    source_path: str,
    target_wav_path: str,
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
) -> None:
    """
    Ingests an arbitrary audio file, enforces size limit, inspects stream,
    converts to 16 kHz mono PCM WAV, and validates against validate_audio contract.
    """
    if not os.path.exists(source_path):
        raise AudioIngestionError("Uploaded audio file does not exist.")

    file_size = os.path.getsize(source_path)
    if file_size == 0:
        raise AudioIngestionError("Uploaded audio file is empty (0 bytes).")
    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        raise AudioIngestionError(f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.")

    # 1. Fast path: Is it already a compliant 16 kHz mono PCM WAV?
    try:
        validate_audio(source_path)
        if os.path.abspath(source_path) != os.path.abspath(target_wav_path):
            shutil.copyfile(source_path, target_wav_path)
        return
    except Exception:
        # Needs decoding / resampling / channel mixing
        pass

    # 2. Try standard audio decoding (librosa / soundfile)
    success = decode_with_librosa_or_soundfile(source_path, target_wav_path)
    if success:
        try:
            validate_audio(target_wav_path)
            return
        except Exception:
            pass

    # 3. Universal PyAV fallback (decodes M4A, AAC, WebM, MP4, Opus, WMA, etc.)
    try:
        decode_with_pyav(source_path, target_wav_path)
        validate_audio(target_wav_path)
    except AudioIngestionError:
        raise
    except Exception as e:
        raise AudioIngestionError(f"Could not decode audio into canonical 16 kHz mono WAV: {e}")


@contextlib.contextmanager
def normalized_audio_context(
    upload_stream_or_path,
    filename_hint: str = "upload.audio",
    temp_dir: str = "artifacts",
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
) -> Generator[str, None, None]:
    """
    Context manager that saves an uploaded stream/file, converts to 16 kHz mono WAV,
    yields the normalized WAV path, and guarantees complete cleanup of temporary files.
    """
    os.makedirs(temp_dir, exist_ok=True)
    session_id = uuid.uuid4().hex
    raw_path = os.path.join(temp_dir, f"raw_{session_id}_{os.path.basename(filename_hint)}")
    norm_path = os.path.join(temp_dir, f"norm_{session_id}.wav")

    try:
        # Write input to raw_path
        if isinstance(upload_stream_or_path, str):
            if not os.path.exists(upload_stream_or_path):
                raise AudioIngestionError(f"File not found: {upload_stream_or_path}")
            shutil.copyfile(upload_stream_or_path, raw_path)
        elif hasattr(upload_stream_or_path, "read"):
            with open(raw_path, "wb") as f_out:
                shutil.copyfileobj(upload_stream_or_path, f_out)
        else:
            raise AudioIngestionError("Invalid input: must be file path or stream.")

        ingest_audio_file(raw_path, norm_path, max_size_bytes=max_size_bytes)
        yield norm_path

    finally:
        for p in (raw_path, norm_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
