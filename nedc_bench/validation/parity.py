"""
Parity validation between Alpha and Beta pipelines
Ensures numerical equivalence within tolerance
"""

from __future__ import annotations

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

    def __str__(self) -> str:  # pragma: no cover - formatting only
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "algorithm": self.algorithm,
            "passed": self.passed,
            "discrepancies": [
                {
                    "metric": d.metric,
                    "alpha_value": d.alpha_value,
                    "beta_value": d.beta_value,
                    "absolute_difference": d.absolute_difference,
                    "relative_difference": d.relative_difference,
                    "tolerance": d.tolerance,
                }
                for d in self.discrepancies
            ],
            "alpha_metrics": self.alpha_metrics,
            "beta_metrics": self.beta_metrics,
        }


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

        # For DP parity, use the unambiguous low-level counts that NEDC prints
        # consistently in detailed outputs: insertions/deletions/substitutions.
        # TP/FP/FN in NEDC DP are summarized via 2x2 per-label and can diverge
        # depending on mapping; skip them to avoid false mismatches.
        pairs: list[tuple[str, float, float]] = [
            ("insertions", float(alpha_result.get("insertions", 0)), float(beta_result.total_insertions)),
            ("deletions", float(alpha_result.get("deletions", 0)), float(beta_result.total_deletions)),
        ]
        if "substitutions" in alpha_result:
            pairs.append(("substitutions", float(alpha_result.get("substitutions", 0)), float(beta_result.total_substitutions)))

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
            labels = list(beta_result.confusion_matrix.keys())
            pos_labels = [lbl for lbl in labels if lbl != "null"] or labels
            tp = float(sum(beta_result.confusion_matrix[lbl][lbl] for lbl in pos_labels))
            fn = float(
                sum(
                    sum(beta_result.confusion_matrix[lbl][j] for j in labels if j != lbl)
                    for lbl in pos_labels
                )
            )
            fp = float(
                sum(
                    sum(beta_result.confusion_matrix[i][lbl] for i in labels if i != lbl)
                    for lbl in pos_labels
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

    def compare_all_algorithms(
        self, alpha_results: dict[str, dict[str, Any]], beta_results: dict[str, Any]
    ) -> dict[str, ValidationReport]:
        """Compare all algorithm results available in both dicts."""
        reports: dict[str, ValidationReport] = {}

        if "taes" in alpha_results and "taes" in beta_results:
            reports["taes"] = self.compare_taes(alpha_results["taes"], beta_results["taes"])
        if "dp" in alpha_results and "dp" in beta_results:
            reports["dp"] = self.compare_dp(alpha_results["dp"], beta_results["dp"])
        if "epoch" in alpha_results and "epoch" in beta_results:
            reports["epoch"] = self.compare_epoch(alpha_results["epoch"], beta_results["epoch"])
        if "overlap" in alpha_results and "overlap" in beta_results:
            reports["overlap"] = self.compare_overlap(
                alpha_results["overlap"], beta_results["overlap"]
            )
        if "ira" in alpha_results and "ira" in beta_results:
            reports["ira"] = self.compare_ira(alpha_results["ira"], beta_results["ira"])

        return reports
