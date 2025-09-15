"""Metrics utilities shared across scripts and orchestration."""

from __future__ import annotations


def fa_per_24h(
    false_positives: float, total_duration_seconds: float, epoch_duration: float | None = None
) -> float:
    """Compute FA/24h according to NEDC definitions.

    - For epoch-based algorithms: FP are in epoch units; multiply by epoch_duration.
    - For event/DP/overlap/taes: FP are event counts; do not scale by epoch_duration.
    - Returns 0 if total_duration_seconds is 0 or negative.
    """
    if total_duration_seconds <= 0:
        return 0.0
    numerator = false_positives * (epoch_duration if epoch_duration is not None else 1.0)
    return float(numerator) / float(total_duration_seconds) * 86400.0
