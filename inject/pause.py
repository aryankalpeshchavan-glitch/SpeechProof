import sys
from pathlib import Path

import soundfile as sf
import numpy as np


def inject_pause(input_wav, output_wav, pause_sec=1.0, position_sec=None):
    """
    Insert a controlled silence into a WAV file.

    input_wav  : original WAV
    output_wav : modified WAV
    pause_sec  : duration of inserted silence
    position_sec : where to insert the pause
    """

    audio, sample_rate = sf.read(input_wav)

    # Convert stereo to mono
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if position_sec is None:
        position_sec = len(audio) / sample_rate / 2

    position_sec = max(0, min(position_sec, len(audio) / sample_rate))

    insert_sample = int(position_sec * sample_rate)
    pause_samples = int(pause_sec * sample_rate)

    silence = np.zeros(pause_samples, dtype=audio.dtype)

    modified_audio = np.concatenate([
        audio[:insert_sample],
        silence,
        audio[insert_sample:]
    ])

    sf.write(output_wav, modified_audio, sample_rate)

    print("Pause injection successful!")
    print(f"Input : {input_wav}")
    print(f"Output: {output_wav}")
    print(f"Pause : {pause_sec} seconds")
    print(f"Position: {position_sec:.2f} seconds")


if __name__ == "__main__":
    inject_pause(
        "data/real/sample_speech.wav",
        "data/injected/sample_pause_1s.wav",
        pause_sec=1.0,
        position_sec=2.0
    )

    input_wav = Path(sys.argv[1])
    output_wav = Path(sys.argv[2])

    pause_sec = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
    position_sec = float(sys.argv[4]) if len(sys.argv) >= 5 else None

    if not input_wav.exists():
        print(f"ERROR: Input file not found: {input_wav}")
        sys.exit(1)

    inject_pause(
        input_wav,
        output_wav,
        pause_sec,
        position_sec
    )