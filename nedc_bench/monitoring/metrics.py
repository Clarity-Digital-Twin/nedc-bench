from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

Counter: Any
Gauge: Any
Histogram: Any

try:  # pragma: no cover - import guard for test envs without dependency
    from prometheus_client import (
        Counter as _PromCounter,
        Gauge as _PromGauge,
        Histogram as _PromHistogram,
    )
    Counter = _PromCounter
    Gauge = _PromGauge
    Histogram = _PromHistogram
except Exception:  # pragma: no cover - provide no-op fallback
    class _NoopMetric:
        def labels(self, **_: Any) -> _NoopMetric:
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
            return None

        def observe(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
            return None

    def _counter(*_args: Any, **_kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    def _gauge(*_args: Any, **_kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    def _histogram(*_args: Any, **_kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    Counter = _counter
    Gauge = _gauge
    Histogram = _histogram


evaluation_counter = Counter(
    "nedc_evaluations_total",
    "Total number of evaluations",
    ["algorithm", "pipeline", "status"],
)
evaluation_duration = Histogram(
    "nedc_evaluation_duration_seconds",
    "Evaluation duration (s)",
    ["algorithm", "pipeline"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)
parity_failures = Counter(
    "nedc_parity_failures_total", "Total parity failures", ["algorithm"]
)
active_evaluations = Gauge(
    "nedc_active_evaluations", "Currently running evaluations"
)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def track_evaluation(algorithm: str, pipeline: str) -> Callable[[F], F]:
    """Decorator to track an async evaluation function with fixed labels.

    Intended for simple cases where labels are static at decoration time.
    """

    def decorator(func: F) -> F:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            active_evaluations.inc()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                evaluation_counter.labels(
                    algorithm=algorithm, pipeline=pipeline, status="success"
                ).inc()
                return result
            except Exception:
                evaluation_counter.labels(
                    algorithm=algorithm, pipeline=pipeline, status="error"
                ).inc()
                raise
            finally:
                evaluation_duration.labels(algorithm=algorithm, pipeline=pipeline).observe(
                    time.time() - start
                )
                active_evaluations.dec()

        return wrapper  # type: ignore[return-value]

    return decorator


async def track_evaluation_dynamic(
    algorithm: str, pipeline: str, coro: Callable[[], Awaitable[Any]]
) -> Any:
    """Helper to track a single async call with dynamic labels."""
    active_evaluations.inc()
    start = time.time()
    try:
        result = await coro()
        evaluation_counter.labels(algorithm=algorithm, pipeline=pipeline, status="success").inc()
        return result
    except Exception:
        evaluation_counter.labels(algorithm=algorithm, pipeline=pipeline, status="error").inc()
        raise
    finally:
        evaluation_duration.labels(algorithm=algorithm, pipeline=pipeline).observe(
            time.time() - start
        )
        active_evaluations.dec()
