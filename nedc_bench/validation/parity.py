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
        if self.passed:
            return f"✅ {self.algorithm} Parity PASSED"
        lines = [
            f"❌ {self.algorithm} Parity FAILED",
            f"Found {len(self.discrepancies)} discrepancies:",
        ]
        lines.extend(
            f"  - {d.metric}: Alpha={d.alpha_value:.6f}, Beta={d.beta_value:.6f}, Diff={d.absolute_difference:.2e}"
            for d in self.discrepancies
        )
        return "\n".join(lines)


class ParityValidator:
    """Validate parity between Alpha and Beta pipeline results"""

    def __init__(self, tolerance: float = 1e-10):
        self.tolerance = tolerance

    # ---------------------- TAES (fractional floats) ----------------------
    def compare_taes(
        self, alpha_result: dict[str, Any], beta_result: TAESResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Round counts to NEDC aggregation precision (summary typically prints 2 decimals)
        alpha_tp = round(float(alpha_result.get("true_positives", 0.0)), 2)
        alpha_fp = round(float(alpha_result.get("false_positives", 0.0)), 2)
        alpha_fn = round(float(alpha_result.get("false_negatives", 0.0)), 2)

        beta_tp = round(float(beta_result.true_positives), 2)
        beta_fp = round(float(beta_result.false_positives), 2)
        beta_fn = round(float(beta_result.false_negatives), 2)

        # Counts-first comparison (floats with atol)
        for name, a, b in (
            ("true_positives", alpha_tp, beta_tp),
            ("false_positives", alpha_fp, beta_fp),
            ("false_negatives", alpha_fn, beta_fn),
        ):
            if abs(a - b) > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        # Recompute metrics centrally from same-rounded counts
        def mm(tp: float, fp: float, fn: float) -> tuple[float, float, float]:
            sen = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            pre = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 0.0 if (pre + sen) == 0 else 2 * (pre * sen) / (pre + sen)
            return sen, pre, f1

        alpha_sen, alpha_pre, alpha_f1 = mm(alpha_tp, alpha_fp, alpha_fn)
        beta_sen, beta_pre, beta_f1 = mm(beta_tp, beta_fp, beta_fn)

        for name, a, b in (
            ("sensitivity", alpha_sen, beta_sen),
            ("precision", alpha_pre, beta_pre),
            ("f1_score", alpha_f1, beta_f1),
        ):
            if abs(a - b) > self.tolerance:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
                        tolerance=self.tolerance,
                    )
                )

        return ValidationReport(
            algorithm="TAES",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics={
                "true_positives": alpha_tp,
                "false_positives": alpha_fp,
                "false_negatives": alpha_fn,
                "sensitivity": alpha_sen,
                "precision": alpha_pre,
                "f1_score": alpha_f1,
            },
            beta_metrics={
                "true_positives": beta_tp,
                "false_positives": beta_fp,
                "false_negatives": beta_fn,
                "sensitivity": beta_sen,
                "precision": beta_pre,
                "f1_score": beta_f1,
            },
        )

    # ---------------------- DP Alignment (integers) ----------------------
    def compare_dp(
        self, alpha_result: dict[str, Any], beta_result: DPAlignmentResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Primary integer counts from Alpha (parser provides totals)
        pairs: list[tuple[str, float, float]] = [
            (
                "true_positives",
                float(alpha_result.get("true_positives", 0)),
                float(beta_result.true_positives),
            ),
            (
                "false_positives",
                float(alpha_result.get("false_positives", 0)),
                float(beta_result.false_positives),
            ),
            (
                "false_negatives",
                float(alpha_result.get("false_negatives", 0)),
                float(beta_result.false_negatives),
            ),
            (
                "insertions",
                float(alpha_result.get("insertions", 0)),
                float(beta_result.total_insertions),
            ),
            (
                "deletions",
                float(alpha_result.get("deletions", 0)),
                float(beta_result.total_deletions),
            ),
        ]

        # Include substitutions if Alpha exposed them (from summary_dpalign.txt)
        if "substitutions" in alpha_result:
            pairs.append((
                "substitutions",
                float(alpha_result.get("substitutions", 0)),
                float(beta_result.total_substitutions),
            ))

        for name, a, b in pairs:
            if abs(a - b) > 0.0:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
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
                "substitutions": beta_result.total_substitutions,
            },
        )

    # ---------------------- Epoch (integers) ----------------------
    def compare_epoch(
        self, alpha_result: dict[str, Any], beta_result: EpochResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        alpha_cm = alpha_result.get("confusion") or {}
        if alpha_cm:
            for rlabel, row in beta_result.confusion_matrix.items():
                for clabel, bcount in row.items():
                    acount = float(alpha_cm.get(rlabel, {}).get(clabel, 0))
                    if abs(acount - float(bcount)) > 0.0:
                        discrepancies.append(
                            DiscrepancyReport(
                                metric=f"confusion[{rlabel},{clabel}]",
                                alpha_value=acount,
                                beta_value=float(bcount),
                                absolute_difference=abs(acount - float(bcount)),
                                relative_difference=abs(acount - float(bcount))
                                / max(abs(acount), 1e-16),
                                tolerance=0.0,
                            )
                        )
        else:
            # Fall back to aggregate counts from Beta confusion
            # Map: TP=sum diag (non-null), FP=sum column off-diag, FN=sum row off-diag
            labels = list(beta_result.confusion_matrix.keys())
            pos_labels = [l for l in labels if l != "null"] or labels
            tp = float(sum(beta_result.confusion_matrix[l][l] for l in pos_labels))
            fn = float(
                sum(
                    sum(beta_result.confusion_matrix[l][j] for j in labels if j != l)
                    for l in pos_labels
                )
            )
            fp = float(
                sum(
                    sum(beta_result.confusion_matrix[i][l] for i in labels if i != l)
                    for l in pos_labels
                )
            )

            for name, a, b in (
                ("true_positives", float(alpha_result.get("true_positives", 0)), tp),
                ("false_positives", float(alpha_result.get("false_positives", 0)), fp),
                ("false_negatives", float(alpha_result.get("false_negatives", 0)), fn),
            ):
                if abs(a - b) > 0.0:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=name,
                            alpha_value=a,
                            beta_value=b,
                            absolute_difference=abs(a - b),
                            relative_difference=abs(a - b) / max(abs(a), 1e-16),
                            tolerance=0.0,
                        )
                    )

        return ValidationReport(
            algorithm="EPOCH",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={"confusion": beta_result.confusion_matrix},
        )

    # ---------------------- Overlap (integers) ----------------------
    def compare_overlap(
        self, alpha_result: dict[str, Any], beta_result: OverlapResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Prefer direct totals if Alpha exposed them; else map to TP/FP/FN
        if {"hits", "misses", "false_alarms"}.issubset(alpha_result.keys()):
            pairs = [
                ("total_hits", float(alpha_result.get("hits", 0)), float(beta_result.total_hits)),
                (
                    "total_misses",
                    float(alpha_result.get("misses", 0)),
                    float(beta_result.total_misses),
                ),
                (
                    "total_false_alarms",
                    float(alpha_result.get("false_alarms", 0)),
                    float(beta_result.total_false_alarms),
                ),
            ]
        else:
            pairs = [
                (
                    "true_positives",
                    float(alpha_result.get("true_positives", 0)),
                    float(beta_result.total_hits),
                ),
                (
                    "false_negatives",
                    float(alpha_result.get("false_negatives", 0)),
                    float(beta_result.total_misses),
                ),
                (
                    "false_positives",
                    float(alpha_result.get("false_positives", 0)),
                    float(beta_result.total_false_alarms),
                ),
            ]

        for name, a, b in pairs:
            if abs(a - b) > 0.0:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
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
                "total_misses": beta_result.total_misses,
                "total_false_alarms": beta_result.total_false_alarms,
            },
        )

    # ---------------------- IRA (floats for kappa) ----------------------
    def compare_ira(self, alpha_result: dict[str, Any], beta_result: IRAResult) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Compare kappas with modest tolerance (Alpha prints to 4 decimals)
        alpha_multi = float(alpha_result.get("multi_class_kappa", alpha_result.get("kappa", 0.0)))
        beta_multi = float(beta_result.multi_class_kappa)
        if abs(alpha_multi - beta_multi) > 1e-4:
            discrepancies.append(
                DiscrepancyReport(
                    metric="multi_class_kappa",
                    alpha_value=alpha_multi,
                    beta_value=beta_multi,
                    absolute_difference=abs(alpha_multi - beta_multi),
                    relative_difference=abs(alpha_multi - beta_multi)
                    / max(abs(alpha_multi), 1e-16),
                    tolerance=1e-4,
                )
            )

        alpha_per = alpha_result.get("per_label_kappa", {})
        for label, b in beta_result.per_label_kappa.items():
            a = float(alpha_per.get(label, 0.0))
            if abs(a - b) > 1e-4:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=f"kappa[{label}]",
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
                        tolerance=1e-4,
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

        # Kappa values - Alpha is rounded to 4 decimals; use looser tolerance
        alpha_multi_kappa = float(
            alpha_result.get("multi_class_kappa", alpha_result.get("kappa", 0.0))
        )
        beta_multi_kappa = float(beta_result.multi_class_kappa)

        if abs(alpha_multi_kappa - beta_multi_kappa) > 1e-4:
            discrepancies.append(
                DiscrepancyReport(
                    metric="multi_class_kappa",
                    alpha_value=alpha_multi_kappa,
                    beta_value=beta_multi_kappa,
                    absolute_difference=abs(alpha_multi_kappa - beta_multi_kappa),
                    relative_difference=abs(alpha_multi_kappa - beta_multi_kappa)
                    / max(abs(alpha_multi_kappa), 1e-16),
                    tolerance=1e-4,
                )
            )

        # Per-label kappas
        alpha_per_label = alpha_result.get("per_label_kappa", {})
        for label, beta_kappa in beta_result.per_label_kappa.items():
            alpha_kappa = float(alpha_per_label.get(label, 0.0))
            if abs(alpha_kappa - beta_kappa) > 1e-4:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=f"kappa[{label}]",
                        alpha_value=alpha_kappa,
                        beta_value=beta_kappa,
                        absolute_difference=abs(alpha_kappa - beta_kappa),
                        relative_difference=abs(alpha_kappa - beta_kappa)
                        / max(abs(alpha_kappa), 1e-16),
                        tolerance=1e-4,
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
        if self.passed:
            return f"✅ {self.algorithm} Parity PASSED"
        lines = [
            f"❌ {self.algorithm} Parity FAILED",
            f"Found {len(self.discrepancies)} discrepancies:",
        ]
        lines.extend(
            f"  - {d.metric}: Alpha={d.alpha_value:.6f}, Beta={d.beta_value:.6f}, Diff={d.absolute_difference:.2e}"
            for d in self.discrepancies
        )
        return "\n".join(lines)


class ParityValidator:
    """Validate parity between Alpha and Beta pipeline results"""

    def __init__(self, tolerance: float = 1e-10):
        self.tolerance = tolerance

    # ---------------------- TAES (fractional) ----------------------
    def compare_taes(
        self, alpha_result: dict[str, Any], beta_result: TAESResult
    ) -> ValidationReport:
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

        return ValidationReport(
            algorithm="TAES",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics={
                "true_positives": alpha_tp,
                "false_positives": alpha_fp,
                "false_negatives": alpha_fn,
                "sensitivity": alpha_sen,
                "precision": alpha_pre,
                "f1_score": alpha_f1,
            },
            beta_metrics={
                "true_positives": beta_tp,
                "false_positives": beta_fp,
                "false_negatives": beta_fn,
                "sensitivity": beta_sen,
                "precision": beta_pre,
                "f1_score": beta_f1,
            },
        )

    # ---------------------- DP (integer) ----------------------
    def compare_dp(
        self, alpha_result: dict[str, Any], beta_result: DPAlignmentResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Alpha provides: true_positives, false_positives, false_negatives, insertions, deletions
        # Prefer detailed counts from dedicated file if available
        a_ins = float(alpha_result.get("insertions", 0))
        a_del = float(alpha_result.get("deletions", 0))
        a_hits = float(alpha_result.get("hits", alpha_result.get("true_positives", 0)))
        a_subs = float(alpha_result.get("substitutions", 0))

        checks = [
            ("hits", a_hits, float(beta_result.hits)),
            ("insertions", a_ins, float(beta_result.total_insertions)),
            ("deletions", a_del, float(beta_result.total_deletions)),
            ("substitutions", a_subs, float(beta_result.total_substitutions)),
        ]
        for name, a, b in checks:
            if abs(a - b) > 0.0:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
                        tolerance=0.0,
                    )
                )

        return ValidationReport(
            algorithm="DP_ALIGNMENT",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "insertions": beta_result.total_insertions,
                "deletions": beta_result.total_deletions,
                # DP derived metrics (e.g., sensitivity) in NEDC summary
                # are computed from per-label 2x2 tables and do not
                # directly correspond to raw hit/miss counts. We compare
                # only raw integer counts for parity.
            },
        )

    # ---------------------- Epoch (integer) ----------------------
    def _aggregate_tp_fp_fn_tn(self, cm: dict[str, dict[str, int]]) -> dict[str, float]:
        labels = list(cm.keys())
        row_sums = {r: sum(cm[r].values()) for r in labels}
        col_sums = {c: sum(cm[r][c] for r in labels) for c in labels}
        total = sum(row_sums.values())
        tp = sum(cm[l][l] for l in labels)
        fn = sum(row_sums[l] - cm[l][l] for l in labels)
        fp = sum(col_sums[l] - cm[l][l] for l in labels)
        tn = total - tp - fp - fn
        return {"tp": float(tp), "fp": float(fp), "fn": float(fn), "tn": float(tn)}

    def compare_epoch(
        self, alpha_result: dict[str, Any], beta_result: EpochResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # If Alpha exposes confusion, compare exactly; else compare aggregated counts
        alpha_cm = alpha_result.get("confusion") or {}
        if alpha_cm:
            for r, row in beta_result.confusion_matrix.items():
                for c, b in row.items():
                    a = float(alpha_cm.get(r, {}).get(c, 0))
                    if abs(a - float(b)) > 0.0:
                        discrepancies.append(
                            DiscrepancyReport(
                                metric=f"confusion[{r},{c}]",
                                alpha_value=a,
                                beta_value=float(b),
                                absolute_difference=abs(a - float(b)),
                                relative_difference=abs(a - float(b)) / max(abs(a), 1e-16),
                                tolerance=0.0,
                            )
                        )
        else:
            # If Alpha doesn't expose counts, compare per-label metrics for
            # the SEIZ class (NEDC prints these in the main summary)
            cm = beta_result.confusion_matrix
            if "seiz" in cm:
                pos = "seiz"
            else:
                # fallback: first non-null label
                labels = [k for k in cm if k != "null"]
                pos = labels[0] if labels else next(iter(cm))
            labels = list(cm.keys())
            tp = float(cm[pos][pos])
            fn = float(sum(cm[pos][j] for j in labels if j != pos))
            fp = float(sum(cm[i][pos] for i in labels if i != pos))
            tn = float(sum(cm[i][j] for i in labels for j in labels if pos not in {i, j}))

            # Compute per-label metrics
            metrics = {}
            metrics["sensitivity"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            metrics["accuracy"] = (
                (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
            )
            prec = metrics["precision"]
            rec = metrics["sensitivity"]
            metrics["f1_score"] = 0.0 if (prec + rec) == 0 else 2 * (prec * rec) / (prec + rec)

            for m in ["sensitivity", "precision", "f1_score", "accuracy"]:
                a = float(alpha_result.get(m, 0.0))
                b = float(metrics[m])
                if abs(a - b) > 1e-4:
                    discrepancies.append(
                        DiscrepancyReport(
                            metric=m,
                            alpha_value=a,
                            beta_value=b,
                            absolute_difference=abs(a - b),
                            relative_difference=abs(a - b) / max(abs(a), 1e-16),
                            tolerance=1e-4,
                        )
                    )

        return ValidationReport(
            algorithm="EPOCH",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={"confusion": beta_result.confusion_matrix},
        )

    # ---------------------- Overlap (integer) ----------------------
    def compare_overlap(
        self, alpha_result: dict[str, Any], beta_result: OverlapResult
    ) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Prefer totals if Alpha parser exposed them; else fall back to TP/FP/FN
        if {"hits", "misses", "false_alarms"}.issubset(alpha_result.keys()):
            pairs = [
                ("total_hits", float(alpha_result.get("hits", 0)), float(beta_result.total_hits)),
                (
                    "total_misses",
                    float(alpha_result.get("misses", 0)),
                    float(beta_result.total_misses),
                ),
                (
                    "total_false_alarms",
                    float(alpha_result.get("false_alarms", 0)),
                    float(beta_result.total_false_alarms),
                ),
            ]
        else:
            pairs = [
                (
                    "true_positives",
                    float(alpha_result.get("true_positives", 0)),
                    float(beta_result.total_hits),
                ),
                (
                    "false_positives",
                    float(alpha_result.get("false_positives", 0)),
                    float(beta_result.total_false_alarms),
                ),
                (
                    "false_negatives",
                    float(alpha_result.get("false_negatives", 0)),
                    float(beta_result.total_misses),
                ),
            ]

        for name, a, b in pairs:
            if abs(a - b) > 0.0:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=name,
                        alpha_value=a,
                        beta_value=b,
                        absolute_difference=abs(a - b),
                        relative_difference=abs(a - b) / max(abs(a), 1e-16),
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
                "total_misses": beta_result.total_misses,
                "total_false_alarms": beta_result.total_false_alarms,
            },
        )

    # ---------------------- IRA (kappa floats; confusion optional) ----------------------
    def compare_ira(self, alpha_result: dict[str, Any], beta_result: IRAResult) -> ValidationReport:
        discrepancies: list[DiscrepancyReport] = []

        # Compare kappa values (floats)
        a_multi = float(alpha_result.get("kappa", alpha_result.get("multi_class_kappa", 0.0)))
        b_multi = float(beta_result.multi_class_kappa)
        if abs(a_multi - b_multi) > 1e-4:
            discrepancies.append(
                DiscrepancyReport(
                    metric="multi_class_kappa",
                    alpha_value=a_multi,
                    beta_value=b_multi,
                    absolute_difference=abs(a_multi - b_multi),
                    relative_difference=abs(a_multi - b_multi) / max(abs(a_multi), 1e-16),
                    tolerance=1e-4,
                )
            )

        a_pl = alpha_result.get("per_label_kappa", {})
        for lbl, bval in beta_result.per_label_kappa.items():
            aval = float(a_pl.get(lbl, bval))
            if abs(aval - float(bval)) > 1e-4:
                discrepancies.append(
                    DiscrepancyReport(
                        metric=f"kappa[{lbl}]",
                        alpha_value=aval,
                        beta_value=float(bval),
                        absolute_difference=abs(aval - float(bval)),
                        relative_difference=abs(aval - float(bval)) / max(abs(aval), 1e-16),
                        tolerance=1e-4,
                    )
                )

        return ValidationReport(
            algorithm="IRA",
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies,
            alpha_metrics=alpha_result,
            beta_metrics={
                "confusion": beta_result.confusion_matrix,
                "multi_class_kappa": beta_result.multi_class_kappa,
                "per_label_kappa": beta_result.per_label_kappa,
            },
        )
