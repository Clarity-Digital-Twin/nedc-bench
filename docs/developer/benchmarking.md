# Performance Benchmarking

## Benchmarking Tools

- `pytest-benchmark`: micro-benchmarking inside tests. Mark tests with `@pytest.mark.benchmark`.
- Make targets:
  - `make benchmark` runs `pytest benchmarks/ --benchmark-only --benchmark-autosave` if a `benchmarks/` folder exists.
  - Alternatively run `pytest -m benchmark --benchmark-only` to execute marked tests anywhere in `tests/`.

## Performance Metrics

- Algorithm runtime per file (TP/FP/FN computation time).
- Beta vs Alpha speedup (use `alpha_time`, `beta_time`, `speedup` fields in evaluation results).
- API latency (P50/P95) and throughput via external load tools if needed.

## Example Benchmark Test

```python
import pytest
from nedc_bench.algorithms.taes import TAESScorer


@pytest.mark.benchmark
def test_taes_performance(benchmark, ref_events, hyp_events):
    scorer = TAESScorer()
    result = benchmark(scorer.score, ref_events, hyp_events)
    assert result.true_positives >= 0.0
```

## Optimization Tips

- Pre-sort events by start time to reduce scans when possible.
- Reuse data structures in tight loops to avoid unnecessary allocations.
- Use int counts for DP/Epoch/Overlap and float64 for TAES.
- Keep inclusive boundary checks consistent to minimize branching.

## Market Research: SzCORE Benchmarking Platform

Insights extracted from `docs/archive/technical/SZCORE_ANALYSIS.md`:

- **Submission Model** – Algorithms are packaged as Docker images with YAML
  metadata validated against a JSON schema; this aligns with our plan to
  standardise evaluation inputs.
- **CI/CD Workflow** – Contributions go through PR-driven validation (schema
  checks, image pulls, output format validation). Consider adopting a similar
  GitHub Actions gate for community submissions.
- **Evaluation Framework** – Multiple datasets and result JSON artefacts enable
  longitudinal comparisons. We should ensure parity snapshots are versioned so
  regressions surface quickly.
- **Infrastructure Practices** – Minimal sample data, volume-mounted inputs, and
  non-privileged containers are industry norms we already follow in Docker/K8s
  guides.
- **Opportunities for NEDC-BENCH** – Extend metadata to capture resource
  requirements, add local development helpers (e.g., `make test-algorithm`), and
  track versioned benchmarking results to tell a stronger story in future
  research documentation.
