"""
Parity validation between Alpha and Beta pipelines
Ensures numerical equivalence within tolerance
"""

from dataclasses import dataclass
from typing import Any

from nedc_bench.algorithms.dp_alignment import DPAlignmentResult
from nedc_bench.algorithms.epoch import EpochResult
from nedc_bench.algorithms.ira import IRAResult
from nedc_bench.algorithms.overlap import OverlapResult
from nedc_bench.algorithms.taes import TAESResult
from nedc_bench.algorithms.dp_alignment import DPAlignmentResult
from nedc_bench.algorithms.epoch import EpochResult
from nedc_bench.algorithms.overlap import OverlapResult
from nedc_bench.algorithms.ira import IRAResult


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

    def compare_dp(self, alpha_result: dict[str, Any], beta_result: DPAlignmentResult) -> ValidationReport:
        """Compare DP results: integer counts must match exactly."""
        discrepancies: list[DiscrepancyReport] = []

        # Primary DP counts from Alpha parser
        # Alpha TP/FP/FN may differ due to different counting
        # Compare raw counts instead
        alpha_tp = float(alpha_result.get("true_positives", 0))
        alpha_fp = float(alpha_result.get("false_positives", 0))
        alpha_fn = float(alpha_result.get("false_negatives", 0))
        alpha_ins = float(alpha_result.get("insertions", 0))
        alpha_del = float(alpha_result.get("deletions", 0))

        # Beta maps: TP=hits, FP=insertions, FN=deletions+substitutions
        for name, alpha_val, beta_val in [
            ("true_positives", alpha_tp, float(beta_result.true_positives)),
            ("false_positives", alpha_fp, float(beta_result.false_positives)),
            ("false_negatives", alpha_fn, float(beta_result.false_negatives)),
            ("insertions", alpha_ins, float(beta_result.total_insertions)),
            ("deletions", alpha_del, float(beta_result.total_deletions)),
        ]:
            abs_diff = abs(alpha_val - beta_val)
            if abs_diff > 0.0:  # ints must match exactly
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=alpha_val,
                        beta_value=beta_val,
                        absolute_difference=abs_diff,
                        relative_difference=abs_diff / max(abs(alpha_val), 1e-16),
                        tolerance=0.0,
                    )
                )

        return ValidationReport(
            algorithm="DP_ALIGNMENT",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "true_positives": beta_result.true_positives,
                "false_positives": beta_result.false_positives,
                "false_negatives": beta_result.false_negatives,
                "insertions": beta_result.total_insertions,
                "deletions": beta_result.total_deletions,
            },
        )

    def compare_epoch(self, alpha_result: dict[str, Any], beta_result: EpochResult) -> ValidationReport:
        """Compare Epoch results: integer confusion matrix entries must match exactly."""
        discrepancies: list[DiscrepancyReport] = []

        # Alpha confusion matrix expected under key names or counts
        # We compare aggregate counts if confusion not available
        # Try confusion-like keys first
        alpha_cm = alpha_result.get("confusion") or {}

        if alpha_cm:
            for rlabel, row in beta_result.confusion_matrix.items():
                for clabel, bcount in row.items():
                    acount = float(alpha_cm.get(rlabel, {}).get(clabel, 0))
                    abs_diff = abs(acount - float(bcount))
                    if abs_diff > 0.0:
                        discrepancies.append(
                            DiscrepancyReport(
                                metric=f"confusion[{rlabel},{clabel}]",
                                alpha_value=acount,
                                beta_value=float(bcount),
                                absolute_difference=abs_diff,
                                relative_difference=abs_diff / max(abs(acount), 1e-16),
                                tolerance=0.0,
                            )
                        )
        else:
            # Fall back to high-level counts if Alpha parser doesn't expose confusion
            for name, a in (
                ("true_positives", float(alpha_result.get("true_positives", 0))),
                ("false_positives", float(alpha_result.get("false_positives", 0))),
                ("false_negatives", float(alpha_result.get("false_negatives", 0))),
            ):
                b = {
                    "true_positives": float(sum(v for k, v in beta_result.hits.items() if k != "null")),
                    "false_positives": float(sum(beta_result.false_alarms.values())),
                    "false_negatives": float(sum(beta_result.misses.values())),
                }[name]
                abs_diff = abs(a - b)
                if abs_diff > 0.0:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=name,
                            alpha_value=a,
                            beta_value=b,
                            absolute_difference=abs_diff,
                            relative_difference=abs_diff / max(abs(a), 1e-16),
                            tolerance=0.0,
                        )
                    )

        return ValidationReport(
            algorithm="EPOCH",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "confusion": beta_result.confusion_matrix,
                "hits": beta_result.hits,
                "misses": beta_result.misses,
                "false_alarms": beta_result.false_alarms,
            },
        )

    def compare_overlap(self, alpha_result: dict[str, Any], beta_result: OverlapResult) -> ValidationReport:
        """Compare Overlap results: integer totals must match exactly."""
        discrepancies: list[DiscrepancyReport] = []
        for name, a, b in (
            ("true_positives", float(alpha_result.get("true_positives", 0)), float(beta_result.total_hits)),
            ("false_positives", float(alpha_result.get("false_positives", 0)), float(beta_result.total_false_alarms)),
            ("false_negatives", float(alpha_result.get("false_negatives", 0)), float(beta_result.total_misses)),
        ):
            abs_diff = abs(a - b)
            if abs_diff > 0.0:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs_diff,
                        relative_difference=abs_diff / max(abs(a), 1e-16),
                        tolerance=0.0,
                    )
                )
        return ValidationReport(
            algorithm="OVERLAP",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "total_hits": beta_result.total_hits,
                "total_false_alarms": beta_result.total_false_alarms,
                "total_misses": beta_result.total_misses,
            },
        )

    def compare_ira(self, alpha_result: dict[str, Any], beta_result: IRAResult) -> ValidationReport:
        """Compare IRA results: confusion ints exact; kappas floats with atol."""
        discrepancies: list[DiscrepancyReport] = []

        # Confusion matrix if Alpha parser provides one (often IRA only in summary)
        alpha_cm = alpha_result.get("confusion") or {}
        for rlabel, row in beta_result.confusion_matrix.items():
            for clabel, bcount in row.items():
                acount = float(alpha_cm.get(rlabel, {}).get(clabel, 0))
                abs_diff = abs(acount - float(bcount))
                if abs_diff > 0.0:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=f"confusion[{rlabel},{clabel}]",
                            alpha_value=acount,
                            beta_value=float(bcount),
                            absolute_difference=abs_diff,
                            relative_difference=abs_diff / max(abs(acount), 1e-16),
                            tolerance=0.0,
                        )
                    )

        # Kappa values: FLOATS with absolute tolerance
        alpha_kappa = float(alpha_result.get("kappa", 0.0))
        abs_diff = abs(alpha_kappa - float(beta_result.multi_class_kappa))
        if abs_diff > self.tolerance:
            discrepancies.append(
                DiscrepancyReport(
                    metric="kappa",
                    alpha_value=alpha_kappa,
                    beta_value=float(beta_result.multi_class_kappa),
                    absolute_difference=abs_diff,
                    relative_difference=abs_diff / max(abs(alpha_kappa), 1e-16),
                    tolerance=self.tolerance,
                )
            )

        # Per-label kappas if present in Alpha result
        alpha_pl = alpha_result.get("per_label_kappa", {})
        for label, bval in beta_result.per_label_kappa.items():
            aval = float(alpha_pl.get(label, bval))
            abs_diff = abs(aval - float(bval))
            if abs_diff > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=f"kappa[{label}]",
                        alpha_value=aval,
                        beta_value=float(bval),
                        absolute_difference=abs_diff,
                        relative_difference=abs_diff / max(abs(aval), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        return ValidationReport(
            algorithm="IRA",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "kappa": beta_result.multi_class_kappa,
                "per_label_kappa": beta_result.per_label_kappa,
            },
        )

    def compare_dp(
        self, alpha_result: dict[str, Any], beta_result: DPAlignmentResult
    ) -> ValidationReport:
        """
        Compare DP Alignment results - INTEGER counts must match exactly

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: DPAlignmentResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies: list[DiscrepancyReport] = []

        # DP uses INTEGER counts - must match exactly
        for name, alpha_key, beta_attr in [
            ("hits", "hits", "hits"),
            ("total_insertions", "insertions", "total_insertions"),
            ("total_deletions", "deletions", "total_deletions"),
            ("total_substitutions", "substitutions", "total_substitutions"),
        ]:
            alpha_val = int(alpha_result.get(alpha_key, 0))
            beta_val = int(getattr(beta_result, beta_attr, 0))

            if alpha_val != beta_val:  # Exact match required for integers
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=float(alpha_val),
                        beta_value=float(beta_val),
                        absolute_difference=abs(alpha_val - beta_val),
                        relative_difference=abs(alpha_val - beta_val) / max(abs(alpha_val), 1),
                        tolerance=0,  # No tolerance for integers
                    )
                )

        # Compute derived metrics for comparison
        alpha_sen = float(alpha_result.get("sensitivity", 0.0))
        beta_tp = beta_result.hits
        beta_fn = beta_result.total_deletions + beta_result.total_substitutions
        beta_sen = beta_tp / (beta_tp + beta_fn) if (beta_tp + beta_fn) > 0 else 0.0

        if abs(alpha_sen - beta_sen) > self.tolerance:
            discrepancies.append(
                DiscrepancyReport(
                    metric="sensitivity",
                    alpha_value=alpha_sen,
                    beta_value=beta_sen,
                    absolute_difference=abs(alpha_sen - beta_sen),
                    relative_difference=abs(alpha_sen - beta_sen) / max(abs(alpha_sen), 1e-16),
                    tolerance=self.tolerance,
                )
            )

        return ValidationReport(
            algorithm="DP_Alignment",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "hits": beta_result.hits,
                "total_insertions": beta_result.total_insertions,
                "total_deletions": beta_result.total_deletions,
                "total_substitutions": beta_result.total_substitutions,
                "sensitivity": beta_sen,
            },
        )

    def compare_epoch(
        self, alpha_result: dict[str, Any], beta_result: EpochResult
    ) -> ValidationReport:
        """
        Compare Epoch results - INTEGER confusion matrix

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: EpochResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies: list[DiscrepancyReport] = []

        # All confusion matrix entries must match EXACTLY (integers)
        alpha_confusion = alpha_result.get("confusion", {})
        for ref_label in beta_result.confusion_matrix:
            for hyp_label in beta_result.confusion_matrix[ref_label]:
                alpha_val = int(alpha_confusion.get(ref_label, {}).get(hyp_label, 0))
                beta_val = int(beta_result.confusion_matrix[ref_label][hyp_label])

                if alpha_val != beta_val:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=f"confusion[{ref_label}][{hyp_label}]",
                            alpha_value=float(alpha_val),
                            beta_value=float(beta_val),
                            absolute_difference=abs(alpha_val - beta_val),
                            relative_difference=abs(alpha_val - beta_val) / max(abs(alpha_val), 1),
                            tolerance=0,
                        )
                    )

        return ValidationReport(
            algorithm="Epoch",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={"confusion_matrix": beta_result.confusion_matrix},
        )

    def compare_overlap(
        self, alpha_result: dict[str, Any], beta_result: OverlapResult
    ) -> ValidationReport:
        """
        Compare Overlap results - INTEGER counts

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: OverlapResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies: list[DiscrepancyReport] = []

        # Check total counts (integers)
        for name, alpha_key, beta_attr in [
            ("total_hits", "hits", "total_hits"),
            ("total_misses", "misses", "total_misses"),
            ("total_false_alarms", "false_alarms", "total_false_alarms"),
        ]:
            alpha_val = int(alpha_result.get(alpha_key, 0))
            beta_val = int(getattr(beta_result, beta_attr, 0))

            if alpha_val != beta_val:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=float(alpha_val),
                        beta_value=float(beta_val),
                        absolute_difference=abs(alpha_val - beta_val),
                        relative_difference=abs(alpha_val - beta_val) / max(abs(alpha_val), 1),
                        tolerance=0,
                    )
                )

        return ValidationReport(
            algorithm="Overlap",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "total_hits": beta_result.total_hits,
                "total_misses": beta_result.total_misses,
                "total_false_alarms": beta_result.total_false_alarms,
            },
        )

    def compare_ira(self, alpha_result: dict[str, Any], beta_result: IRAResult) -> ValidationReport:
        """
        Compare IRA - INTEGER confusion, FLOAT kappa

        Args:
            alpha_result: Dictionary from Alpha pipeline
            beta_result: IRAResult from Beta pipeline

        Returns:
            ValidationReport with comparison details
        """
        discrepancies: list[DiscrepancyReport] = []

        # Confusion matrix - EXACT match (integers)
        alpha_confusion = alpha_result.get("confusion", {})
        for ref_label in beta_result.confusion_matrix:
            for hyp_label in beta_result.confusion_matrix[ref_label]:
                alpha_val = int(alpha_confusion.get(ref_label, {}).get(hyp_label, 0))
                beta_val = int(beta_result.confusion_matrix[ref_label][hyp_label])

                if alpha_val != beta_val:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=f"confusion[{ref_label}][{hyp_label}]",
                            alpha_value=float(alpha_val),
                            beta_value=float(beta_val),
                            absolute_difference=abs(alpha_val - beta_val),
                            relative_difference=abs(alpha_val - beta_val) / max(abs(alpha_val), 1),
                            tolerance=0,
                        )
                    )

        # Kappa values - use tolerance (floats)
        alpha_multi_kappa = float(alpha_result.get("multi_class_kappa", 0.0))
        beta_multi_kappa = float(beta_result.multi_class_kappa)

        if abs(alpha_multi_kappa - beta_multi_kappa) > self.tolerance:
            discrepancies.append(
                DiscrepancyReport(
                    metric="multi_class_kappa",
                    alpha_value=alpha_multi_kappa,
                    beta_value=beta_multi_kappa,
                    absolute_difference=abs(alpha_multi_kappa - beta_multi_kappa),
                    relative_difference=abs(alpha_multi_kappa - beta_multi_kappa)
                    / max(abs(alpha_multi_kappa), 1e-16),
                    tolerance=self.tolerance,
                )
            )

        # Per-label kappas
        alpha_per_label = alpha_result.get("per_label_kappa", {})
        for label, beta_kappa in beta_result.per_label_kappa.items():
            alpha_kappa = float(alpha_per_label.get(label, 0.0))
            if abs(alpha_kappa - beta_kappa) > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=f"kappa[{label}]",
                        alpha_value=alpha_kappa,
                        beta_value=beta_kappa,
                        absolute_difference=abs(alpha_kappa - beta_kappa),
                        relative_difference=abs(alpha_kappa - beta_kappa)
                        / max(abs(alpha_kappa), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        return ValidationReport(
            algorithm="IRA",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "confusion_matrix": beta_result.confusion_matrix,
                "multi_class_kappa": beta_result.multi_class_kappa,
                "per_label_kappa": beta_result.per_label_kappa,
            },
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

        # TAES comparison (already implemented)
        if "taes" in alpha_results and "taes" in beta_results:
            reports["taes"] = self.compare_taes(alpha_results["taes"], beta_results["taes"])

        # DP Alignment comparison
        if "dp" in alpha_results and "dp" in beta_results:
            reports["dp"] = self.compare_dp(alpha_results["dp"], beta_results["dp"])

        # Epoch comparison
        if "epoch" in alpha_results and "epoch" in beta_results:
            reports["epoch"] = self.compare_epoch(alpha_results["epoch"], beta_results["epoch"])

        # Overlap comparison
        if "overlap" in alpha_results and "overlap" in beta_results:
            reports["overlap"] = self.compare_overlap(
                alpha_results["overlap"], beta_results["overlap"]
            )

        # IRA comparison
        if "ira" in alpha_results and "ira" in beta_results:
            reports["ira"] = self.compare_ira(alpha_results["ira"], beta_results["ira"])

        return reports
