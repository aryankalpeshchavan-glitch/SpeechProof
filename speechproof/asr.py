from faster_whisper import WhisperModel
import json
import sys
from pathlib import Path

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

def transcribe(wav):
    segments, info = model.transcribe(
        wav,
        beam_size=1,
        temperature=0,
        condition_on_previous_text=False,
        word_timestamps=True
    )

    words = []

    for segment in segments:
        if segment.words is None:
            continue

        for word in segment.words:
            text = word.word.strip()

            if text:
                words.append({
                    "word": text,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3)
                })

    return words


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python speechproof\\asr.py <audio.wav>")
        sys.exit(1)

    wav = Path(sys.argv[1])

    if not wav.exists():
        print(f"ERROR: Audio file not found: {wav}")
        sys.exit(1)

    words = transcribe(str(wav))

    output = {
        "audio_file": str(wav),
        "word_count": len(words),
        "words": words
    }

    print(json.dumps(output, indent=2))
