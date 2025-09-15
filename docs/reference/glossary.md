# Glossary

## EEG Terms
- Event: A labeled time interval, e.g., seizure (`seiz`) or background (`bckg`).
- Epoch: Fixed-duration time window used for IRA/Epoch scoring (e.g., 0.25s).

## Algorithm Terms
- DP Alignment (DP): Dynamic programming alignment of reference vs hypothesis events; counts TP/FP/FN by optimal sequence alignment.
- Epoch-based (Epoch): Converts events into fixed-length epochs and compares labels per epoch.
- Overlap (OVLP): Counts matches if any overlap exists between corresponding events.
- Time-Aligned Event Scoring (TAES): Measures detection quality using time-aligned overlap; yields floating-point TP/FP/FN.
- IRA: Inter-Rater Agreement; computes Cohen’s kappa per label and multi-class kappa from aggregated confusion.

## Metrics
- TP/FP/FN: True/False Positives/Negatives. For TAES they may be fractional; others are integers.
- Sensitivity: `TP / (TP + FN) * 100`.
- FA/24h: False alarms per 24 hours. For Epoch, FP is scaled by `epoch_duration` per NEDC rules.
