# SpeechProof Architecture

## Production Scoring Path
audio.wav -> ASR -> Acoustic Feature Extraction -> Frozen Rubric -> Evidence Builder -> Evidence JSON

## Evaluation Path
audio/data -> Crash-Test Lab (T1-T9) -> rating_card.json -> Dashboard

## Reproducibility Rules
- No fake benchmark numbers.
- Output hashing must use deterministic JSON serialization.
- Production scoring MUST NOT read injection manifests.
- The pipeline structure is deterministic.
- Repeated transcript text, segment counts, and word counts are reproducible.
- Residual ASR timestamp nondeterminism may be observed across identical runs and is considered acceptable within defined tolerances.
