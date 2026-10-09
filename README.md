# SpeechProof

SpeechProof is a platform for evaluating and scoring speech acoustics objectively using AI.

## What SpeechProof Does

SpeechProof extracts and scores speech audio dimensions based on a standard rubric. It establishes transparency by calculating a secure SHA-256 hash across both the audio and the generated evidence, persistently recording it in a local SQLite ledger for subsequent verification and audit.

## Production Scoring Pipeline

The pipeline runs as follows:
1. **Transcribe**: Uses `faster-whisper` to transcribe the audio into words and segments.
2. **Extract Features**: Leverages `librosa` and `parselmouth` to extract acoustic features (e.g., duration, pitch variety, pacing).
3. **Score**: Maps the extracted raw features into normalized scoring dimensions (0-100 scale).
4. **Build Evidence**: Compiles an evidence JSON containing scores, raw metrics, run identifiers, and structural metadata.
5. **Persist**: Stores the scoring metadata into a local `db/ledger.sqlite` database.

## Supported Input Format and Sample Rate

Audio must be passed through a strict validation pre-flight:
- Format: `.wav`
- Channels: Mono (1 channel)
- Sample Rate: Exactly 16 kHz

## Current Scoring Dimensions

SpeechProof successfully measures:
- `pace`
- `pausing`
- `pitch`
- `energy`

**Note**: The `fluency` dimension is currently **unavailable** because `filler_rate_per_min` extraction is not yet supported by the pipeline. The `fluency_unavailable` flag is explicitly populated in the output payload's `quality_flags`. The `overall_score` average mathematically bounds strictly to the dimensions actually measured.

## Evidence Hashing & Local SQLite Persistence

For traceability and tamper-proofing, an evidence payload hash is derived from the audio SHA-256 footprint and the actual measured scores. This payload is stored in `db/ledger.sqlite`. A deterministic `sha256_json()` function allows any third-party to rigorously verify that an exported evidence JSON file natively matches its recorded local history.

## How to Install and Run Tests

Installation via Conda:
```bash
conda env create -f environment.yml
conda activate speechproof
```

Running the test suite:
```bash
# Optional: prepend PYTHONPATH="." on Windows/PowerShell
pytest -q
```

## How to Execute a Real GPU Smoke Test

Execute the end-to-end integration smoke test directly against the GPU pipeline:
```bash
python smoke_test_runner.py
```
*Note: Ensure you have an authorized test wav file present at `data/real/aryan_test.wav` and a compatible CUDA runtime.*

## Limitations & Future Validation

- **T1-T9 campaigns** have not yet been completed.
- There is a strict distinction between **operational tests** (verifying software stability) and **research-validity evaluation**.
- We do not currently claim scientific validity for the produced scores until extensive evaluation and dataset verification has been empirically completed on the platform.
