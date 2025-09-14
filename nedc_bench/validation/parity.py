"""
Parity validation between Alpha and Beta pipelines
Ensures numerical equivalence within tolerance
"""

from dataclasses import dataclass
from typing import Any

from nedc_bench.algorithms.taes import TAESResult


@dataclass
class DiscrepancyReport:
    """Single metric discrepancy between pipelines"""

    metric: str
    alpha_value: float
    beta_value: float
    absolute_difference: float
    relative_difference: float
    tolerance: float

    @property
    def within_tolerance(self) -> bool:
        """Check if difference is within acceptable tolerance"""
        return self.absolute_difference <= self.tolerance


@dataclass
class ValidationReport:
    """Complete validation report"""

    algorithm: str
    passed: bool
    discrepancies: list[DiscrepancyReport]
    alpha_metrics: dict[str, Any]
    beta_metrics: dict[str, Any]

    def __str__(self) -> str:
        """Human-readable report"""
        if self.passed:
            return f"✅ {self.algorithm} Parity PASSED"

        lines = [f"❌ {self.algorithm} Parity FAILED"]
        lines.append(f"Found {len(self.discrepancies)} discrepancies:")

        lines.extend(
            f"  - {disc.metric}: "
            f"Alpha={disc.alpha_value:.6f}, "
            f"Beta={disc.beta_value:.6f}, "
            f"Diff={disc.absolute_difference:.2e}"
            for disc in self.discrepancies
        )

        return "\n".join(lines)


class ParityValidator:
    """Validate parity between Alpha and Beta pipeline results"""

    def __init__(self, tolerance: float = 1e-10):
        """
        Initialize validator

        Args:
            tolerance: Maximum acceptable absolute difference
        """
        self.tolerance = tolerance

    def compare_taes(
        self, alpha_result: dict[str, Any], beta_result: TAESResult
    ) -> ValidationReport:
        """
        Compare TAES results from both pipelines

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: TAESResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies = []

        # Define metrics to compare (counts-first, then floats)
        metrics_map = {
            "sensitivity": beta_result.sensitivity,
            "precision": beta_result.precision,
            "f1_score": beta_result.f1_score,
            "true_positives": beta_result.true_positives,
            "false_positives": beta_result.false_positives,
            "false_negatives": beta_result.false_negatives,
        }

        beta_metrics = {}

        for metric_name, beta_value in metrics_map.items():
            beta_metrics[metric_name] = beta_value

            # Get Alpha value
            alpha_value = alpha_result.get(metric_name)
            if alpha_value is None:
                continue

            # Compare ints exactly
            if metric_name in {"true_positives", "false_positives", "false_negatives"}:
                if int(alpha_value) != int(beta_value):
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=metric_name,
                            alpha_value=float(alpha_value),
                            beta_value=float(beta_value),
                            absolute_difference=abs(float(alpha_value) - float(beta_value)),
                            relative_difference=0.0,
                            tolerance=0.0,
                        )
                    )
                continue

            # Floats: absolute tolerance only
            if isinstance(alpha_value, (int, float)):
                alpha_float = float(alpha_value)
                beta_float = float(beta_value)
                abs_diff = abs(alpha_float - beta_float)
                rel_diff = abs_diff / max(abs(alpha_float), 1e-16)
                if abs_diff > self.tolerance:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=metric_name,
                            alpha_value=alpha_float,
                            beta_value=beta_float,
                            absolute_difference=abs_diff,
                            relative_difference=rel_diff,
                            tolerance=self.tolerance,
                        )
                    )

        return ValidationReport(
            algorithm="TAES",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics=beta_metrics,
        )

    def compare_all_algorithms(
        self, alpha_results: dict[str, dict], beta_results: dict[str, Any]
    ) -> dict[str, ValidationReport]:
        """
        Compare all algorithm results

        Returns:
            Dictionary of ValidationReports by algorithm
        """
        reports = {}

        # TAES comparison
        if "taes" in alpha_results and "taes" in beta_results:
            reports["taes"] = self.compare_taes(alpha_results["taes"], beta_results["taes"])

        # Future: Add other algorithms (epoch, overlap, dpalign, ira)
        # reports['overlap'] = self.compare_overlap(...)

        return reports
