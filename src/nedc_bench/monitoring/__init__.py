"""Monitoring and metrics instrumentation for NEDC-BENCH API.

This module provides Prometheus-compatible metrics tracking for evaluation workflows.
All metrics gracefully degrade to no-ops when prometheus_client is unavailable.

## Metrics Available

- **evaluation_counter**: Total number of evaluations (labels: algorithm, pipeline, status)
- **evaluation_duration**: Evaluation duration histogram (labels: algorithm, pipeline)
- **parity_failures**: Total parity failures counter (labels: algorithm)
- **active_evaluations**: Gauge of currently running evaluations

## Usage

### Decorator (static labels):
```python
from nedc_bench.monitoring import track_evaluation

@track_evaluation(algorithm="taes", pipeline="beta")
async def my_eval():
    ...
```

### Helper (dynamic labels):
```python
from nedc_bench.monitoring import track_evaluation_dynamic

result = await track_evaluation_dynamic(
    algorithm=alg,
    pipeline=pipe,
    coro=lambda: evaluate(ref, hyp)
)
```

## Dependencies

- Optional: `prometheus_client` (falls back to no-op metrics if missing)
"""

from __future__ import annotations

from nedc_bench.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    active_evaluations,
    evaluation_counter,
    evaluation_duration,
    parity_failures,
    track_evaluation,
    track_evaluation_dynamic,
)

__all__ = [
    # Metric types (for type hints)
    "Counter",
    "Gauge",
    "Histogram",
    # Metric instances
    "evaluation_counter",
    "evaluation_duration",
    "parity_failures",
    "active_evaluations",
    # Tracking helpers
    "track_evaluation",
    "track_evaluation_dynamic",
]
