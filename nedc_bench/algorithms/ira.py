"""IRA (Inter-Rater Agreement) algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Kappa computation separate for per-label and multi-class
- Open/Closed: Extensible kappa formulas
- Liskov Substitution: Consistent result interface
- Interface Segregation: Focused methods for 2x2 and NxN matrices
- Dependency Inversion: Works with label sequences abstraction
"""

from dataclasses import dataclass


@dataclass
class IRAResult:
    """NEDC IRA results with INTEGER confusion, FLOAT kappa

    Per NEDC source:
    - Confusion matrix uses INTEGERS (counts)
    - Kappa values are FLOATS (agreement scores)
    """

    # Confusion matrix (INTEGERS)
    confusion_matrix: dict[str, dict[str, int]]

    # Per-label kappa (FLOATS)
    per_label_kappa: dict[str, float]

    # Multi-class kappa (FLOAT)
    multi_class_kappa: float

    # Labels
    labels: list[str]


class IRAScorer:
    """NEDC-exact inter-rater agreement

    Implements the IRA algorithm from nedc_eeg_eval_ira.py
    using epoch-based approach with integer confusion matrix
    and float kappa values.
    """

    def score(self, ref_labels: list[str], hyp_labels: list[str]) -> IRAResult:
        """NEDC IRA using epoch-based approach

        Implements NEDC lines 22-24: uses epoch-based scoring internally.
        Builds integer confusion matrix, computes float kappa values.

        Args:
            ref_labels: Reference label sequence
            hyp_labels: Hypothesis label sequence

        Returns:
            IRAResult with integer confusion matrix and float kappa values
        """
        # Handle empty sequences
        if not ref_labels or not hyp_labels:
            return IRAResult(
                confusion_matrix={}, per_label_kappa={}, multi_class_kappa=0.0, labels=[]
            )

        # Build INTEGER confusion matrix
        labels = sorted(set(ref_labels + hyp_labels))
        confusion = {l1: {l2: 0 for l2 in labels} for l1 in labels}

        # Ensure same length for confusion matrix
        min_len = min(len(ref_labels), len(hyp_labels))

        for i in range(min_len):
            ref = ref_labels[i]
            hyp = hyp_labels[i]
            confusion[ref][hyp] += 1  # INTEGER increment

        # Compute per-label kappa (NEDC lines 499-540)
        per_label_kappa = {}
        for label in labels:
            kappa = self._compute_label_kappa(confusion, label, labels)
            per_label_kappa[label] = kappa

        # Compute multi-class kappa (NEDC lines 548-583)
        multi_kappa = self._compute_multi_class_kappa(confusion, labels)

        return IRAResult(
            confusion_matrix=confusion,
            per_label_kappa=per_label_kappa,
            multi_class_kappa=multi_kappa,
            labels=labels,
        )

    def _compute_label_kappa(
        self, confusion: dict[str, dict[str, int]], label: str, labels: list[str]
    ) -> float:
        """Per-label kappa using 2x2 matrix (lines 499-540)

        Computes Cohen's kappa for a single label vs all others.

        Args:
            confusion: Full confusion matrix
            label: The label to compute kappa for
            labels: All labels

        Returns:
            Float kappa value for this label
        """
        # Build 2x2 matrix
        # a = true positive (both agree it's this label)
        a = float(confusion[label][label]) if label in confusion else 0.0

        # b = false positive (ref says label, hyp says other)
        b = (
            sum(confusion[label].get(l2, 0) for l2 in labels if l2 != label)
            if label in confusion
            else 0.0
        )

        # c = false negative (ref says other, hyp says label)
        c = sum(confusion.get(l2, {}).get(label, 0) for l2 in labels if l2 != label)

        # d = true negative (both agree it's not this label)
        d = sum(
            confusion.get(l2, {}).get(l3, 0)
            for l2 in labels
            for l3 in labels
            if label not in {l2, l3}
        )

        # Compute total
        denom = a + b + c + d
        if denom == 0:
            return 0.0

        # Compute observed agreement
        p_o = (a + d) / denom

        # Compute expected agreement
        p_yes = ((a + b) / denom) * ((a + c) / denom)
        p_no = ((c + d) / denom) * ((b + d) / denom)
        p_e = p_yes + p_no

        # Compute kappa
        if (1 - p_e) == 0:
            return 1.0 if p_o == p_e else 0.0

        return (p_o - p_e) / (1 - p_e)

    def _compute_multi_class_kappa(
        self, confusion: dict[str, dict[str, int]], labels: list[str]
    ) -> float:
        """Multi-class kappa (lines 548-583)

        Computes overall Cohen's kappa for all classes.

        Args:
            confusion: Full confusion matrix
            labels: All labels

        Returns:
            Float multi-class kappa value
        """
        # Handle empty case
        if not labels:
            return 0.0

        # Row and column sums
        sum_rows = {}
        sum_cols = {}

        for label in labels:
            # Row sum (sum across columns for this row)
            sum_rows[label] = sum(confusion.get(label, {}).get(l2, 0) for l2 in labels)
            # Column sum (sum across rows for this column)
            sum_cols[label] = sum(confusion.get(l2, {}).get(label, 0) for l2 in labels)

        # Diagonal sum (correct predictions)
        sum_m = sum(confusion.get(label, {}).get(label, 0) for label in labels)

        # Total count
        sum_n = sum(sum_rows.values())

        # Handle empty confusion matrix
        if sum_n == 0:
            return 0.0

        # Sum of products of marginals
        sum_gc = sum(sum_rows[label] * sum_cols[label] for label in labels)

        # Compute kappa
        num = sum_n * sum_m - sum_gc
        denom = sum_n * sum_n - sum_gc

        if denom == 0:
            return 1.0 if num == 0 else 0.0

        return float(num) / float(denom)
