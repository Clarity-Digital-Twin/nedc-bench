"""
Output parsers for NEDC v6.0.0 text output
Converts text-based scoring results to structured JSON
"""
from __future__ import annotations

import re
from pathlib import Path


class BaseParser:
    """Base class for algorithm-specific parsers"""

    def extract_percentage(self, text: str, pattern: str) -> float:
        """Extract percentage value from text"""
        match = re.search(pattern + r':\s+(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1)) / 100.0
        return None

    def extract_float(self, text: str, pattern: str) -> float:
        """Extract float value from text"""
        match = re.search(pattern + r':\s+(\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        return None

    def extract_int(self, text: str, pattern: str) -> int:
        """Extract integer value from text"""
        match = re.search(pattern + r':\s+(\d+)', text)
        if match:
            return int(match.group(1))
        return None


class DPAlignmentParser(BaseParser):
    """Parser for DP Alignment algorithm output"""

    def parse(self, text: str) -> dict:
        """Parse DP Alignment section from summary"""
        result = {}

        # Find DP Alignment section
        dp_section = re.search(
            r'NEDC DP ALIGNMENT SCORING SUMMARY.*?(?=\n={70,}|\Z)',
            text,
            re.DOTALL
        )

        if not dp_section:
            return result

        section_text = dp_section.group(0)

        # Extract metrics
        result['sensitivity'] = self.extract_percentage(section_text, r'Sensitivity \(TPR, Recall\)')
        result['specificity'] = self.extract_percentage(section_text, r'Specificity \(TNR\)')
        result['precision'] = self.extract_percentage(section_text, r'Precision \(PPV\)')
        result['f1_score'] = self.extract_float(section_text, r'F1 Score \(F Ratio\)')
        result['accuracy'] = self.extract_percentage(section_text, r'Accuracy')

        # Extract counts
        result['true_positives'] = self.extract_int(section_text, r'True Positives \(TP\)')
        result['true_negatives'] = self.extract_int(section_text, r'True Negatives \(TN\)')
        result['false_positives'] = self.extract_int(section_text, r'False Positives \(FP\)')
        result['false_negatives'] = self.extract_int(section_text, r'False Negatives \(FN\)')

        result['insertions'] = self.extract_int(section_text, r'Insertions')
        result['deletions'] = self.extract_int(section_text, r'Deletions')

        return result


class EpochParser(BaseParser):
    """Parser for Epoch-based scoring output"""

    def parse(self, text: str) -> dict:
        """Parse Epoch section from summary"""
        result = {}

        # Find Epoch section
        epoch_section = re.search(
            r'NEDC EPOCH SCORING SUMMARY.*?(?=\n={70,}|\Z)',
            text,
            re.DOTALL
        )

        if not epoch_section:
            return result

        section_text = epoch_section.group(0)

        # Extract metrics
        result['sensitivity'] = self.extract_percentage(section_text, r'Sensitivity \(TPR, Recall\)')
        result['specificity'] = self.extract_percentage(section_text, r'Specificity \(TNR\)')
        result['precision'] = self.extract_percentage(section_text, r'Precision \(PPV\)')
        result['f1_score'] = self.extract_float(section_text, r'F1 Score \(F Ratio\)')
        result['accuracy'] = self.extract_percentage(section_text, r'Accuracy')
        result['mcc'] = self.extract_float(section_text, r'Matthews \(MCC\)')

        # Extract counts
        result['true_positives'] = self.extract_int(section_text, r'True Positives \(TP\)')
        result['true_negatives'] = self.extract_int(section_text, r'True Negatives \(TN\)')
        result['false_positives'] = self.extract_int(section_text, r'False Positives \(FP\)')
        result['false_negatives'] = self.extract_int(section_text, r'False Negatives \(FN\)')

        return result


class OverlapParser(BaseParser):
    """Parser for Overlap scoring output"""

    def parse(self, text: str) -> dict:
        """Parse Overlap section from summary"""
        result = {}

        # Find Overlap section
        ovlp_section = re.search(
            r'NEDC OVERLAP SCORING SUMMARY.*?(?=\n={70,}|\Z)',
            text,
            re.DOTALL
        )

        if not ovlp_section:
            return result

        section_text = ovlp_section.group(0)

        # Extract metrics
        result['sensitivity'] = self.extract_percentage(section_text, r'Sensitivity \(TPR, Recall\)')
        result['specificity'] = self.extract_percentage(section_text, r'Specificity \(TNR\)')
        result['precision'] = self.extract_percentage(section_text, r'Precision \(PPV\)')
        result['f1_score'] = self.extract_float(section_text, r'F1 Score \(F Ratio\)')
        result['accuracy'] = self.extract_percentage(section_text, r'Accuracy')

        # Extract counts
        result['true_positives'] = self.extract_int(section_text, r'True Positives \(TP\)')
        result['true_negatives'] = self.extract_int(section_text, r'True Negatives \(TN\)')
        result['false_positives'] = self.extract_int(section_text, r'False Positives \(FP\)')
        result['false_negatives'] = self.extract_int(section_text, r'False Negatives \(FN\)')

        return result


class TAESParser(BaseParser):
    """Parser for Time-Aligned Event Scoring output"""

    def parse(self, text: str) -> dict:
        """Parse TAES section from summary or dedicated file"""
        result = {}

        # Find TAES section
        taes_section = re.search(
            r'NEDC TAES SCORING SUMMARY.*?(?=\n={70,}|\Z)',
            text,
            re.DOTALL
        )

        if not taes_section:
            return result

        section_text = taes_section.group(0)

        # Extract metrics
        result['sensitivity'] = self.extract_percentage(section_text, r'Sensitivity \(TPR, Recall\)')
        result['specificity'] = self.extract_percentage(section_text, r'Specificity \(TNR\)')
        result['precision'] = self.extract_percentage(section_text, r'Precision \(PPV\)')
        result['f1_score'] = self.extract_float(section_text, r'F1 Score \(F Ratio\)')
        result['accuracy'] = self.extract_percentage(section_text, r'Accuracy')

        # Extract counts
        result['true_positives'] = self.extract_int(section_text, r'True Positives \(TP\)')
        result['true_negatives'] = self.extract_int(section_text, r'True Negatives \(TN\)')
        result['false_positives'] = self.extract_int(section_text, r'False Positives \(FP\)')
        result['false_negatives'] = self.extract_int(section_text, r'False Negatives \(FN\)')

        return result


class IRAParser(BaseParser):
    """Parser for Inter-Rater Agreement output"""

    def parse(self, text: str) -> dict:
        """Parse IRA section from summary (no separate file)"""
        result: dict = {}

        # Find IRA section
        ira_section = re.search(
            r'NEDC INTER-RATER AGREEMENT SUMMARY.*?(?=\n={70,}|\Z)',
            text,
            re.DOTALL
        )

        if not ira_section:
            return result

        section_text = ira_section.group(0)

        # Kappa may appear as either "Cohen's Kappa" or "Multi-Class Kappa"
        cohens = re.search(r"Cohen's Kappa:\s+(\d+\.?\d*)", section_text)
        if cohens:
            result['kappa'] = float(cohens.group(1))
        else:
            multi = re.search(r'Multi-Class Kappa:\s+(\d+\.?\d*)', section_text)
            if multi:
                result['kappa'] = float(multi.group(1))

        # Per-label Kappa lines: "Label: seiz   Kappa:  0.xxxx"
        per_label = {}
        for m in re.finditer(r'Label:\s+(\w+)\s+Kappa:\s+(\d+\.?\d*)', section_text):
            per_label[m.group(1)] = float(m.group(2))
        if per_label:
            result['per_label_kappa'] = per_label

        return result


class UnifiedOutputParser:
    """Parse all 5 algorithm outputs from NEDC"""

    def __init__(self):
        self.dp_parser = DPAlignmentParser()
        self.epoch_parser = EpochParser()
        self.overlap_parser = OverlapParser()
        self.taes_parser = TAESParser()
        self.ira_parser = IRAParser()

    def parse_summary(self, text: str, output_dir: Path | None = None) -> dict:
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
        results['dp_alignment'] = self.dp_parser.parse(text)
        results['epoch'] = self.epoch_parser.parse(text)
        results['overlap'] = self.overlap_parser.parse(text)
        results['taes'] = self.taes_parser.parse(text)
        results['ira'] = self.ira_parser.parse(text)  # IRA is in main summary

        # If output_dir provided, also check for individual summary files
        if output_dir:
            output_path = Path(output_dir)

            # Check for individual algorithm files
            files_to_check = {
                'dp_alignment': 'summary_dpalign.txt',
                'epoch': 'summary_epoch.txt',
                'overlap': 'summary_ovlp.txt',
                'taes': 'summary_taes.txt'
            }

            for algo, filename in files_to_check.items():
                file_path = output_path / filename
                if file_path.exists():
                    file_text = file_path.read_text()
                    # Parse dedicated file if it has more detail
                    if algo == 'dp_alignment':
                        detailed = self.dp_parser.parse(file_text)
                    elif algo == 'epoch':
                        detailed = self.epoch_parser.parse(file_text)
                    elif algo == 'overlap':
                        detailed = self.overlap_parser.parse(file_text)
                    elif algo == 'taes':
                        detailed = self.taes_parser.parse(file_text)

                    # Merge with existing results (detailed file takes precedence)
                    results[algo].update(detailed)

        return results
