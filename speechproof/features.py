import librosa
import numpy as np
import json
import sys


def extract(wav, words=None):
    y, sr = librosa.load(wav, sr=16000, mono=True)

    duration = len(y) / sr

    # -------------------------
    # RMS / Vocal Energy
    # -------------------------
    rms = librosa.feature.rms(
        y=y,
        frame_length=2048,
        hop_length=512
    )[0]

    rms_db = librosa.amplitude_to_db(
        rms + 1e-10,
        ref=np.max
    )

    # -------------------------
    # Pitch / F0
    # -------------------------
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr
    )

    pitch_values = f0[~np.isnan(f0)]

    if len(pitch_values):
        pitch_mean = float(np.mean(pitch_values))
        pitch_std = float(np.std(pitch_values))

        # Convert F0 variation to semitone variation
        pitch_semitones = 12 * np.log2(
            pitch_values / pitch_mean
        )

        pitch_std_semitones = float(
            np.std(pitch_semitones)
        )
    else:
        pitch_mean = None
        pitch_std = None
        pitch_std_semitones = None

    # -------------------------
    # Word / Speech Features
    # -------------------------
    word_count = len(words) if words else 0

    speech_rate_wpm = 0

    pauses = []
    pause_ratio = 0

    if words and len(words) >= 2:

        for i in range(1, len(words)):
            gap = words[i]["start"] - words[i - 1]["end"]

            if gap >= 0.4:
                pauses.append(gap)

        speech_duration = max(duration, 0.001)
        speech_rate_wpm = (
            word_count / speech_duration * 60
        )

        total_pause_time = sum(pauses)

        pause_ratio = (
            total_pause_time / speech_duration
        )

    # -------------------------
    # Feature Output
    # -------------------------
    features = {
        "sample_rate": sr,
        "duration_sec": round(duration, 3),

        "word_count": word_count,
        # speech_rate_wpm measures words per minute over elapsed recording time, including pauses.
        "speech_rate_wpm": round(
            speech_rate_wpm, 2
        ),

        "pause_count": len(pauses),
        "pause_mean_sec": round(
            float(np.mean(pauses)), 3
        ) if pauses else 0,

        "pause_max_sec": round(
            float(np.max(pauses)), 3
        ) if pauses else 0,

        "pause_ratio": round(
            pause_ratio, 4
        ),

        "relative_rms_db_mean": round(
            float(np.mean(rms_db)), 3
        ),

        "relative_rms_db_std": round(
            float(np.std(rms_db)), 3
        ),

        "pitch_mean_hz": round(
            pitch_mean, 3
        ) if pitch_mean else None,

        "pitch_std_hz": round(
            pitch_std, 3
        ) if pitch_std is not None else None,

        "pitch_std_semitones": round(
            pitch_std_semitones, 3
        ) if pitch_std_semitones is not None else None
    }

    return features


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: python speechproof\\features.py <audio.wav>"
        )
        sys.exit(1)

    result = extract(sys.argv[1])

    print(
        json.dumps(
            result,
            indent=2
        )
    )
