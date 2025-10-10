# Data Formats

## Inputs

- CSV_BI (NEDC event annotation format) is the canonical input for both Alpha and Beta pipelines.
- Reference and Hypothesis files must share the same duration and sampling assumptions used by NEDC.

## Outputs

- Alpha: Text summaries per algorithm under `output/` (when using the NEDC tool).
- Beta: Structured JSON metrics (TP, FP, FN, sensitivity, FA/24h); used by the API responses.

## Conversions

- CSV_BI → internal event lists: handled by `nedc_bench.models.annotations.AnnotationFile.from_csv_bi`.
- Label normalization: NEDC label maps applied so `seiz`/`bckg`/null classes align across pipelines.

## Validation

- Use `scripts/compare_parity.py` to assert Beta JSON totals match parsed Alpha outputs for the same inputs.
