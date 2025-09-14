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

        IMPORTANT: TAES uses fractional scoring, so TP/FP/FN are floats.
        We compare counts first, then recompute metrics centrally.

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: TAESResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies: list[DiscrepancyReport] = []

        # Round counts to NEDC aggregation precision (2 decimals)
        alpha_tp = round(float(alpha_result.get("true_positives", 0.0)), 2)
        alpha_fp = round(float(alpha_result.get("false_positives", 0.0)), 2)
        alpha_fn = round(float(alpha_result.get("false_negatives", 0.0)), 2)

        beta_tp = round(float(beta_result.true_positives), 2)
        beta_fp = round(float(beta_result.false_positives), 2)
        beta_fn = round(float(beta_result.false_negatives), 2)

        # Compare counts first
        for name, a, b in (
            ("true_positives", alpha_tp, beta_tp),
            ("false_positives", alpha_fp, beta_fp),
            ("false_negatives", alpha_fn, beta_fn),
        ):
            abs_diff = abs(a - b)
            if abs_diff > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs_diff,
                        relative_difference=abs_diff / max(abs(a), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        # Compute metrics centrally from the same-rounded counts
        def metrics_from_counts(tp: float, fp: float, fn: float) -> tuple[float, float, float]:
            sen = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            pre = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 0.0 if (pre + sen) == 0 else 2 * (pre * sen) / (pre + sen)
            return sen, pre, f1

        alpha_sen, alpha_pre, alpha_f1 = metrics_from_counts(alpha_tp, alpha_fp, alpha_fn)
        beta_sen, beta_pre, beta_f1 = metrics_from_counts(beta_tp, beta_fp, beta_fn)

        for name, a, b in (
            ("sensitivity", alpha_sen, beta_sen),
            ("precision", alpha_pre, beta_pre),
            ("f1_score", alpha_f1, beta_f1),
        ):
            abs_diff = abs(a - b)
            if abs_diff > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs_diff,
                        relative_difference=abs_diff / max(abs(a), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        beta_metrics = {
            "true_positives": beta_tp,
            "false_positives": beta_fp,
            "false_negatives": beta_fn,
            "sensitivity": beta_sen,
            "precision": beta_pre,
            "f1_score": beta_f1,
        }

        alpha_metrics = {
            "true_positives": alpha_tp,
            "false_positives": alpha_fp,
            "false_negatives": alpha_fn,
            "sensitivity": alpha_sen,
            "precision": alpha_pre,
            "f1_score": alpha_f1,
        }

        return ValidationReport(
            algorithm="TAES",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_metrics,
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
