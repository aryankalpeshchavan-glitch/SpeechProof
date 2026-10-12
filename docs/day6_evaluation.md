# Day 6 — SpeechProof Evaluation

## Objective
Evaluate whether SpeechProof detects changes in speech timing when an artificial pause is inserted into an audio recording.

## Experiment
The original speech recording was compared with a version containing an injected pause. Both recordings were processed using the SpeechProof pipeline.

## Results

| Metric | Original (Run 20) | Injected pause (Run 21) | Change |
|---|---:|---:|---:|
| Overall score | 98.98 | 95.42 | -3.56 |
| Pausing score | 94.9 | 77.1 | -17.8 |

## Interpretation
The injected-pause recording received a lower pausing score and a lower overall score. This indicates that the current scoring system responds to this particular pause-injection test.

## Limitations
- This is a single paired experiment.
- Speech recognition and detected word boundaries may vary between runs.
- The result does not establish general model accuracy or real-world speech-assessment validity.
- Further tests with multiple recordings and pause lengths are required.

## Output
The comparison was exported to `data/pause_comparison.csv`.

## Conclusion
The initial experiment provides evidence that SpeechProof is sensitive to an injected pause. Additional controlled experiments are needed to assess consistency and robustness.