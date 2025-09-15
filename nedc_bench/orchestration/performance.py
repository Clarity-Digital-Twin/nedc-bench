"""Performance monitoring for dual pipeline"""

import statistics
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics for algorithm execution"""

    algorithm: str
    pipeline: str  # 'alpha' or 'beta'
    execution_times: list[float]

    @property
    def mean_time(self) -> float:
        return statistics.mean(self.execution_times)

    @property
    def median_time(self) -> float:
        return statistics.median(self.execution_times)

    @property
    def std_dev(self) -> float:
        return statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0

    @property
    def min_time(self) -> float:
        return min(self.execution_times)

    @property
    def max_time(self) -> float:
        return max(self.execution_times)


class PerformanceMonitor:
    """Monitor and compare pipeline performance"""

    def __init__(self) -> None:
        self.metrics: dict[str, PerformanceMetrics] = {}

    def record_execution(self, algorithm: str, pipeline: str, execution_time: float) -> None:
        """Record an execution time"""
        key = f"{algorithm}_{pipeline}"

        if key not in self.metrics:
            self.metrics[key] = PerformanceMetrics(
                algorithm=algorithm, pipeline=pipeline, execution_times=[]
            )

        self.metrics[key].execution_times.append(execution_time)

    def get_speedup(self, algorithm: str) -> float:
        """Calculate Beta speedup over Alpha"""
        alpha_key = f"{algorithm}_alpha"
        beta_key = f"{algorithm}_beta"

        if alpha_key in self.metrics and beta_key in self.metrics:
            alpha_mean = self.metrics[alpha_key].mean_time
            beta_mean = self.metrics[beta_key].mean_time
            return alpha_mean / beta_mean if beta_mean > 0 else 0.0

        return 0.0

    def generate_report(self) -> str:
        """Generate performance report"""
        lines = ["Performance Report", "=" * 50]

        for metrics in self.metrics.values():
            lines.extend((
                f"\n{metrics.algorithm.upper()} - {metrics.pipeline.capitalize()}",
                f"  Mean: {metrics.mean_time:.4f}s",
                f"  Median: {metrics.median_time:.4f}s",
                f"  Std Dev: {metrics.std_dev:.4f}s",
                f"  Min: {metrics.min_time:.4f}s",
                f"  Max: {metrics.max_time:.4f}s",
            ))

        # Add speedup calculations
        algorithms = set(m.algorithm for m in self.metrics.values())
        lines.extend(("\nSpeedup (Beta vs Alpha)", "-" * 30))

        for algo in algorithms:
            speedup = self.get_speedup(algo)
            if speedup > 0:
                lines.append(f"{algo.upper()}: {speedup:.2f}x")

        return "\n".join(lines)
