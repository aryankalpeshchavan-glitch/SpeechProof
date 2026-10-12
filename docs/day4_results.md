# Day 4 — Reliability Testing

## Tests completed

- **Baseline speech:** Run 20 scored 98.98.
- **Injected-pause speech:** Run 21 scored 95.42. The pausing score decreased from 94.9 to 77.1.
- **Short speech:** Run 22 scored 89.60 and was saved successfully.
- **Evidence integrity:** Run 22 reported `VERIFIED` during pipeline execution.

## Limitations

- The scoring thresholds are provisional and require validation using more speakers and recordings.
- Automatic speech recognition may produce different word counts between runs.
- The existing integrity diagnostic checks Run 11, so Run 22 has not yet been independently checked using that script.

## Conclusion

Day 4 testing demonstrated that SpeechProof can process baseline, pause-injected, and short speech recordings and save their evidence. Further testing is required before treating the scores as validated measures of speaking quality.