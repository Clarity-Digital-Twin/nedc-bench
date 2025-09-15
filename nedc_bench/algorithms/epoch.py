"""Epoch Scoring algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Epoch scoring and compression are separate methods
- Open/Closed: Extensible epoch classification strategy
- Liskov Substitution: Consistent interfaces
- Interface Segregation: Focused methods for each step
- Dependency Inversion: Depend on EventAnnotation abstraction
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class EpochResult:
    """NEDC epoch results with INTEGER confusion matrix

    All counts are integers per NEDC source lines 690-723.
    """
    # Full NxN confusion matrix (all integers)
    confusion_matrix: Dict[str, Dict[str, int]]

    # Per-label counts (all integers)
    hits: Dict[str, int]
    misses: Dict[str, int]
    false_alarms: Dict[str, int]
    insertions: Dict[str, int]  # From NULL_CLASS transitions
    deletions: Dict[str, int]  # To NULL_CLASS transitions

    # Compressed epoch sequences (for debugging)
    compressed_ref: List[str]
    compressed_hyp: List[str]


class EpochScorer:
    """NEDC-exact epoch-based scoring

    Implements the epoch scoring algorithm from nedc_eeg_eval_epoch.py
    with consecutive duplicate compression and NULL_CLASS handling.
    """

    def __init__(self,
                 epoch_duration: float = 1.0,
                 null_class: str = "null"):
        """Initialize with epoch parameters

        Args:
            epoch_duration: Duration of each fixed-width epoch (default 1.0)
            null_class: Label for unclassified epochs (default "null")
        """
        self.epoch_duration = epoch_duration
        self.null_class = null_class

    def score(self, ref_events: List[EventAnnotation],
              hyp_events: List[EventAnnotation],
              file_duration: float) -> EpochResult:
        """NEDC epoch scoring with compression

        Implements NEDC lines 590-730: fixed epochs, compression, confusion matrix.

        Args:
            ref_events: Reference event annotations
            hyp_events: Hypothesis event annotations
            file_duration: Total duration of the file

        Returns:
            EpochResult with integer confusion matrix and compressed sequences
        """
        # Create fixed-window epochs
        epochs = self._create_epochs(file_duration)

        # Classify each epoch
        ref_labels = self._classify_epochs(epochs, ref_events)
        hyp_labels = self._classify_epochs(epochs, hyp_events)

        # CRITICAL: Compress consecutive duplicates (NEDC lines 600-610)
        ref_compressed = self._compress_epochs(ref_labels)
        hyp_compressed = self._compress_epochs(hyp_labels)

        # Build confusion matrix and count errors
        return self._compute_metrics(ref_compressed, hyp_compressed)

    def _create_epochs(self, file_duration: float) -> List[Tuple[float, float]]:
        """Create fixed-width epoch windows

        Args:
            file_duration: Total duration to divide into epochs

        Returns:
            List of (start_time, end_time) tuples
        """
        epochs = []
        current_time = 0.0

        while current_time < file_duration:
            end_time = min(current_time + self.epoch_duration, file_duration)
            epochs.append((current_time, end_time))
            current_time = end_time

        return epochs

    def _classify_epochs(self, epochs: List[Tuple[float, float]],
                        events: List[EventAnnotation]) -> List[str]:
        """Classify each epoch based on overlapping events

        Args:
            epochs: List of (start_time, end_time) tuples
            events: Event annotations to check for overlap

        Returns:
            List of labels, one per epoch
        """
        labels = []

        for epoch_start, epoch_end in epochs:
            # Find overlapping event (if any)
            epoch_label = self.null_class

            for event in events:
                # Check for ANY overlap with this epoch
                if event.stop_time > epoch_start and event.start_time < epoch_end:
                    # Use the label of the first overlapping event found
                    # In case of multiple overlaps, NEDC uses priority/first-found
                    epoch_label = event.label
                    break

            labels.append(epoch_label)

        return labels

    def _compress_epochs(self, labels: List[str]) -> List[str]:
        """Remove consecutive duplicates (NEDC lines 600-610)

        This is a CRITICAL step that distinguishes epoch scoring from
        simple frame-by-frame comparison.

        Args:
            labels: List of epoch labels

        Returns:
            Compressed list with no consecutive duplicates
        """
        if not labels:
            return []

        compressed = [labels[0]]
        for i in range(1, len(labels)):
            if labels[i] != labels[i-1]:
                compressed.append(labels[i])

        return compressed

    def _compute_metrics(self, ref_compressed: List[str],
                        hyp_compressed: List[str]) -> EpochResult:
        """Build confusion matrix and compute metrics

        Implements NEDC lines 690-723: confusion matrix with NULL_CLASS handling.

        Args:
            ref_compressed: Compressed reference labels
            hyp_compressed: Compressed hypothesis labels

        Returns:
            EpochResult with integer confusion matrix
        """
        # Get all unique labels
        all_labels = sorted(set(ref_compressed + hyp_compressed))

        # Initialize confusion matrix (all zeros, integers)
        confusion_matrix = {
            ref_label: {hyp_label: 0 for hyp_label in all_labels}
            for ref_label in all_labels
        }

        # Initialize per-label counts
        hits = {label: 0 for label in all_labels}
        misses = {label: 0 for label in all_labels}
        false_alarms = {label: 0 for label in all_labels}
        insertions = {}
        deletions = {}

        # Ensure sequences are same length for confusion matrix
        # This is done by aligning or padding as needed
        min_len = min(len(ref_compressed), len(hyp_compressed))

        # Build confusion matrix for aligned portion
        for i in range(min_len):
            ref_label = ref_compressed[i]
            hyp_label = hyp_compressed[i]

            # Increment confusion matrix (INTEGER)
            confusion_matrix[ref_label][hyp_label] += 1

            # Update per-label counts
            if ref_label == hyp_label:
                # Hit
                hits[ref_label] += 1
            else:
                # Miss for ref_label, false alarm for hyp_label
                misses[ref_label] += 1
                false_alarms[hyp_label] += 1

                # Track NULL_CLASS transitions (NEDC lines 716-722)
                if ref_label == self.null_class:
                    # Insertion: null -> something
                    if hyp_label not in insertions:
                        insertions[hyp_label] = 0
                    insertions[hyp_label] += 1
                elif hyp_label == self.null_class:
                    # Deletion: something -> null
                    if ref_label not in deletions:
                        deletions[ref_label] = 0
                    deletions[ref_label] += 1

        # Handle remaining unaligned portions
        if len(ref_compressed) > min_len:
            # Remaining ref labels are deletions
            for i in range(min_len, len(ref_compressed)):
                ref_label = ref_compressed[i]
                misses[ref_label] += 1
                if ref_label not in deletions:
                    deletions[ref_label] = 0
                deletions[ref_label] += 1

        if len(hyp_compressed) > min_len:
            # Remaining hyp labels are insertions
            for i in range(min_len, len(hyp_compressed)):
                hyp_label = hyp_compressed[i]
                false_alarms[hyp_label] += 1
                if hyp_label not in insertions:
                    insertions[hyp_label] = 0
                insertions[hyp_label] += 1

        return EpochResult(
            confusion_matrix=confusion_matrix,
            hits=hits,
            misses=misses,
            false_alarms=false_alarms,
            insertions=insertions,
            deletions=deletions,
            compressed_ref=ref_compressed,
            compressed_hyp=hyp_compressed
        )