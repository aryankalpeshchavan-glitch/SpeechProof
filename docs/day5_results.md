# Day 5 — Verification and Robustness Testing

## Completed

- Updated `verify_saved_run.py` to accept a run ID as a command-line argument, defaulting to Run 22.
- Verified saved evidence for Runs 20, 22, and 23.
- Confirmed that modified copies of evidence produce a different SHA-256 hash.
- Tested short speech: Run 22 scored 89.60.
- Tested quiet speech at 50% volume: Run 23 scored 98.98.
- Confirmed that pause injection reduced the pausing score in Run 21.

## Limitations

- The rubric scores are provisional and have not been validated against human ratings.
- A single quiet-speech test does not establish general robustness.
- Hash verification checks evidence consistency, not the authenticity of the original recording.
- More tests are needed across speakers, recording devices, background noise, and speech lengths.