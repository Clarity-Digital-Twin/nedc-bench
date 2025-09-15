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
