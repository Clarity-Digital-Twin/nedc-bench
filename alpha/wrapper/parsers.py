"""
Output parsers for NEDC v6.0.0 text output
Converts text-based scoring results to structured JSON
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class BaseParser:
    """Base class for algorithm-specific parsers"""

    @staticmethod
    def extract_percentage(text: str, pattern: str) -> float | None:
        """Extract percentage value from text"""
        match = re.search(pattern + r":\s+(\d+\.?\d*)%", text)
        if match:
            return float(match.group(1)) / 100.0
        return None

    @staticmethod
    def extract_float(text: str, pattern: str) -> float | None:
        """Extract float value from text"""
        match = re.search(pattern + r":\s+(\d+\.?\d*)", text)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def extract_int(text: str, pattern: str) -> int | None:
        """Extract integer value from text"""
        match = re.search(pattern + r":\s+(\d+)", text)
        if match:
            return int(match.group(1))
        return None


class DPAlignmentParser(BaseParser):
    """Parser for DP Alignment algorithm output"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse DP Alignment from main summary and/or dedicated file.

        - If main summary section is present, extract metrics and 2x2 counts.
        - Regardless, sum per-file Hit/Sub/Ins/Del if present in the text.
        """
        result: dict[str, Any] = {}

        # Optional main summary section
        dp_section = re.search(
            r"NEDC DP ALIGNMENT SCORING SUMMARY.*?(?=\n={70,}|\Z)", text, re.DOTALL
        )
        if dp_section:
            section_text = dp_section.group(0)
            result["sensitivity"] = self.extract_percentage(
                section_text, r"Sensitivity \(TPR, Recall\)"
            )
            result["specificity"] = self.extract_percentage(section_text, r"Specificity \(TNR\)")
            result["precision"] = self.extract_percentage(section_text, r"Precision \(PPV\)")
            result["f1_score"] = self.extract_float(section_text, r"F1 Score \(F Ratio\)")
            result["accuracy"] = self.extract_percentage(section_text, r"Accuracy")

            result["true_positives"] = self.extract_int(section_text, r"True Positives \(TP\)")
            result["true_negatives"] = self.extract_int(section_text, r"True Negatives \(TN\)")
            result["false_positives"] = self.extract_int(section_text, r"False Positives \(FP\)")
            result["false_negatives"] = self.extract_int(section_text, r"False Negatives \(FN\)")
            result["insertions"] = self.extract_int(section_text, r"Insertions")
            result["deletions"] = self.extract_int(section_text, r"Deletions")

        # Always scan for per-file counts from detailed file content
        hits = subs = ins = dels = 0
        for m in re.finditer(
            r"\(\s*Hit:\s*(\d+)\s+Sub:\s*(\d+)\s+Ins:\s*(\d+)\s+Del:\s*(\d+)\s+", text
        ):
            h, s, i, d = m.groups()
            hits += int(h)
            subs += int(s)
            ins += int(i)
            dels += int(d)
        if hits or subs or ins or dels:
            result["hits"] = hits
            result["substitutions"] = subs
            result["insertions"] = ins
            result["deletions"] = dels

        return result


class EpochParser(BaseParser):
    """Parser for Epoch-based scoring output"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse Epoch section from summary

        Prefer metrics and counts from the SUMMARY subsection (totals across labels).
        """
        result: dict[str, Any] = {}

        epoch_section = re.search(r"NEDC EPOCH SCORING SUMMARY.*?(?=\n={70,}|\Z)", text, re.DOTALL)
        if not epoch_section:
            return result

        section_text = epoch_section.group(0)

        # Extract confusion matrix first
        matrix_match = re.search(
            r"NEDC Epoch Confusion Matrix\s*\n\s*Ref/Hyp:.*?\n(.*?)(?=\n\s*PER LABEL|\n\s*\n)",
            section_text,
            re.DOTALL,
        )
        if matrix_match:
            confusion = {}
            matrix_text = matrix_match.group(1)
            # Parse the matrix rows - format is:
            # seiz:     1249.00 ( 78.70%)      338.00 ( 21.30%)
            # bckg:     2303.00 ( 64.53%)     1266.00 ( 35.47%)
            for line in matrix_text.strip().split("\n"):
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        ref_label = parts[0].strip().lower()
                        # Extract numbers (ignoring percentages)
                        nums = re.findall(r"(\d+(?:\.\d+)?)\s*\(", parts[1])
                        if len(nums) >= 2:
                            confusion[ref_label] = {
                                "seiz": int(float(nums[0])),
                                "bckg": int(float(nums[1])),
                            }
            if confusion:
                result["confusion"] = confusion

        # Extract metrics from section (these are summary metrics)
        result["sensitivity"] = self.extract_percentage(
            section_text, r"Sensitivity \(TPR, Recall\)"
        )
        result["specificity"] = self.extract_percentage(section_text, r"Specificity \(TNR\)")
        result["precision"] = self.extract_percentage(section_text, r"Precision \(PPV\)")
        result["f1_score"] = self.extract_float(section_text, r"F1 Score \(F Ratio\)")
        result["accuracy"] = self.extract_percentage(section_text, r"Accuracy")
        result["mcc"] = self.extract_float(section_text, r"Matthews \(MCC\)")

        # Try to narrow to the SUMMARY block for totals
        summary_match = re.search(
            r"SUMMARY:\s*(.*?)(?=\n\s*\n|\Z)", section_text, re.DOTALL | re.IGNORECASE
        )
        summary_text = summary_match.group(1) if summary_match else section_text

        # Extract TOTAL counts from summary
        tp = re.findall(r"True Positives\s*\(TP\)\s*:\s*(\d+)", summary_text)
        tn = re.findall(r"True Negatives\s*\(TN\)\s*:\s*(\d+)", summary_text)
        fp = re.findall(r"False Positives\s*\(FP\)\s*:\s*(\d+)", summary_text)
        fn = re.findall(r"False Negatives\s*\(FN\)\s*:\s*(\d+)", summary_text)

        # If multiple matches (per label), take the last which is likely summary
        if tp:
            result["true_positives"] = int(tp[-1])
        if tn:
            result["true_negatives"] = int(tn[-1])
        if fp:
            result["false_positives"] = int(fp[-1])
        if fn:
            result["false_negatives"] = int(fn[-1])

        return result


class OverlapParser(BaseParser):
    """Parser for Overlap scoring output"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse Overlap from main summary and/or dedicated file."""
        result: dict[str, Any] = {}

        # Optional main summary section
        ovlp_section = re.search(r"NEDC OVERLAP SCORING SUMMARY.*?(?=\n={70,}|\Z)", text, re.DOTALL)
        if ovlp_section:
            section_text = ovlp_section.group(0)
            result["sensitivity"] = self.extract_percentage(
                section_text, r"Sensitivity \(TPR, Recall\)"
            )
            result["specificity"] = self.extract_percentage(section_text, r"Specificity \(TNR\)")
            result["precision"] = self.extract_percentage(section_text, r"Precision \(PPV\)")
            result["f1_score"] = self.extract_float(section_text, r"F1 Score \(F Ratio\)")
            result["accuracy"] = self.extract_percentage(section_text, r"Accuracy")
            result["true_positives"] = self.extract_int(section_text, r"True Positives \(TP\)")
            result["true_negatives"] = self.extract_int(section_text, r"True Negatives \(TN\)")
            result["false_positives"] = self.extract_int(section_text, r"False Positives \(FP\)")
            result["false_negatives"] = self.extract_int(section_text, r"False Negatives \(FN\)")

        # Always sum per-file totals if present
        hits = misses = falses = 0
        for m in re.finditer(
            r"\(\s*Hit:\s*(\d+)\s+Miss:\s*(\d+)\s+False\s+Alarms:\s*(\d+)\s+", text
        ):
            h, mi, fa = m.groups()
            hits += int(h)
            misses += int(mi)
            falses += int(fa)
        if hits or misses or falses:
            result["hits"] = hits
            result["misses"] = misses
            result["false_alarms"] = falses

        return result


class TAESParser(BaseParser):
    """Parser for Time-Aligned Event Scoring output"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse TAES section from summary or dedicated file

        TAES uses fractional scoring, so TP/TN/FP/FN are floats.
        Prefer summary_taes.txt for higher precision (4 decimals)
        over summary.txt (2 decimals).
        """
        result: dict[str, Any] = {}

        # Find TAES section
        taes_section = re.search(r"NEDC TAES SCORING SUMMARY.*?(?=\n={70,}|\Z)", text, re.DOTALL)

        if not taes_section:
            return result

        section_text = taes_section.group(0)

        # Extract metrics
        result["sensitivity"] = self.extract_percentage(
            section_text, r"Sensitivity \(TPR, Recall\)"
        )
        result["specificity"] = self.extract_percentage(section_text, r"Specificity \(TNR\)")
        result["precision"] = self.extract_percentage(section_text, r"Precision \(PPV\)")
        result["f1_score"] = self.extract_float(section_text, r"F1 Score \(F Ratio\)")
        result["accuracy"] = self.extract_percentage(section_text, r"Accuracy")

        # Extract counts - TAES uses floats for fractional scoring
        result["true_positives"] = self.extract_float(section_text, r"True Positives \(TP\)")
        result["true_negatives"] = self.extract_float(section_text, r"True Negatives \(TN\)")
        result["false_positives"] = self.extract_float(section_text, r"False Positives \(FP\)")
        result["false_negatives"] = self.extract_float(section_text, r"False Negatives \(FN\)")

        return result


class IRAParser(BaseParser):
    """Parser for Inter-Rater Agreement output"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse IRA section from summary (no separate file)"""
        result: dict[str, Any] = {}

        # Find IRA section
        ira_section = re.search(
            r"NEDC INTER-RATER AGREEMENT SUMMARY.*?(?=\n={70,}|\Z)", text, re.DOTALL
        )

        if not ira_section:
            return result

        section_text = ira_section.group(0)

        # Kappa may appear as either "Cohen's Kappa" or "Multi-Class Kappa"
        cohens = re.search(r"Cohen's Kappa:\s+(\d+\.?\d*)", section_text)
        if cohens:
            result["kappa"] = float(cohens.group(1))
        else:
            multi = re.search(r"Multi-Class Kappa:\s+(\d+\.?\d*)", section_text)
            if multi:
                result["kappa"] = float(multi.group(1))

        # Per-label Kappa lines: "Label: seiz   Kappa:  0.xxxx"
        per_label = {}
        for m in re.finditer(r"Label:\s+(\w+)\s+Kappa:\s+(\d+\.?\d*)", section_text):
            per_label[m.group(1)] = float(m.group(2))
        if per_label:
            result["per_label_kappa"] = per_label

        return result


class UnifiedOutputParser:
    """Parse all 5 algorithm outputs from NEDC"""

    def __init__(self) -> None:
        self.dp_parser = DPAlignmentParser()
        self.epoch_parser = EpochParser()
        self.overlap_parser = OverlapParser()
        self.taes_parser = TAESParser()
        self.ira_parser = IRAParser()

    def parse_summary(self, text: str, output_dir: Path | None = None) -> dict[str, Any]:
        """
        Parse main summary and individual algorithm files

        Args:
            text: Content of summary.txt
            output_dir: Directory containing output files

        Returns:
            Dictionary with results from all 5 algorithms
        """
        results = {}

        # Parse main summary
        results["dp_alignment"] = self.dp_parser.parse(text)
        results["epoch"] = self.epoch_parser.parse(text)
        results["overlap"] = self.overlap_parser.parse(text)
        results["taes"] = self.taes_parser.parse(text)
        results["ira"] = self.ira_parser.parse(text)  # IRA is in main summary

        # If output_dir provided, also check for individual summary files
        if output_dir:
            output_path = Path(output_dir)

            # Check for individual algorithm files
            files_to_check = {
                "dp_alignment": "summary_dpalign.txt",
                "epoch": "summary_epoch.txt",
                "overlap": "summary_ovlp.txt",
                "taes": "summary_taes.txt",
            }

            for algo, filename in files_to_check.items():
                file_path = output_path / filename
                if file_path.exists():
                    file_text = file_path.read_text()
                    # Parse dedicated file if it has more detail
                    if algo == "dp_alignment":
                        detailed = self.dp_parser.parse(file_text)
                    elif algo == "epoch":
                        detailed = self.epoch_parser.parse(file_text)
                    elif algo == "overlap":
                        detailed = self.overlap_parser.parse(file_text)
                    elif algo == "taes":
                        detailed = self.taes_parser.parse(file_text)

                    # Merge with existing results (detailed file takes precedence)
                    results[algo].update(detailed)

        return results
