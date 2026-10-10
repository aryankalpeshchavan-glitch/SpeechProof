# SpeechProof Protocol Pre-registration

## A. Scorer and Configuration
- **Scorer Version**: 0.1.0
- **Rubric Version**: 0.1
- **Git Revision**: (frozen dynamically at run time)
- **ASR Model**: large-v3 (Whisper)
- **Device**: CUDA (or fallback)
- **Compute Type**: float16 (or fallback)
- **Dimensions**: Pace, Pausing, Pitch, Energy. Fluency is unsupported.

## B. Dataset
- **Authorized Identifiers**: `aryan_test.wav`
- **Data Splits**: All evaluation relies on the N=1 pilot sample (no splits).
- **Consent**: Authorized for automated evaluation only.
- **Flaws**:
  - Pace: 0.7x to 1.3x
  - Volume: -12dB to +12dB
  - Pause: 2.0s insertion
- **Ground-Truth Source**: N/A for human labels; synthetic targets for T4.

## C. Statistical Methods
- **Metric Definitions**: F1 at IoU>=0.5, median onset error, Spearman rho.
- **Confidence Intervals**: 95% Bootstrap for T6, exact permutation test for dose-response.
- **Equivalence Margin (T5)**: Standard Deviation of paired take-to-take differences. (Currently undefined for N=1).
- **Missing Observations**: Ignored via JSON null.
- **Failed Inputs**: Excluded from valid aggregates but counted in failure rates.
- **Pass/Fail Thresholds**: F1 >= 0.7; median onset error <= 0.25s; rho >= 0.5.
- **Conditions**: Test marked INCONCLUSIVE if N < 3. NOT RUN if inputs are missing.

## D. Planned Hypotheses
- **T4 (Localization)**: Expected to exceed IoU>=0.5 with high F1.
- **T5 (Invariance)**: Expected equivalence under volume scaling.
- **T6 (Agreement)**: Positive correlation with human judgments (if data exist).
- **T7 (Group Stability)**: Within-group variance < between-group variance.
- **T8 (MDC95)**: Gate suppresses false-positive improvements.
- **T9 (Gaming Resistance)**: Scorer resists unearned improvements.
- **A1-A5 (Ablations)**: Baselines are expected to underperform the full pipeline.
