"""Epoch Scoring algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Epoch scoring and compression are separate methods
- Open/Closed: Extensible epoch classification strategy
- Liskov Substitution: Consistent interfaces
- Interface Segregation: Focused methods for each step
- Dependency Inversion: Depend on EventAnnotation abstraction
"""

from dataclasses import dataclass

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class EpochResult:
    """NEDC epoch results with INTEGER confusion matrix

    All counts are integers per NEDC source lines 690-723.
    """

    # Full NxN substitution/confusion matrix at sample resolution (all integers)
    confusion_matrix: dict[str, dict[str, int]]

    # Per-label counts (all integers)
    hits: dict[str, int]
    misses: dict[str, int]
    false_alarms: dict[str, int]
    insertions: dict[str, int]  # From NULL_CLASS transitions
    deletions: dict[str, int]  # To NULL_CLASS transitions

    # Compressed epoch sequences (for debugging)
    compressed_ref: list[str]
    compressed_hyp: list[str]

    @property
    def true_positives(self) -> dict[str, int]:
        """Calculate TP for each label from confusion matrix

        TP(label) = confusion_matrix[label][label]
        i.e., reference label correctly classified as same label
        """
        tp = {}
        for label in self.confusion_matrix:
            if label in self.confusion_matrix.get(label, {}):
                tp[label] = self.confusion_matrix[label][label]
            else:
                tp[label] = 0
        return tp

    @property
    def false_positives(self) -> dict[str, int]:
        """Calculate FP for each label from confusion matrix

        FP(label) = sum of all confusion_matrix[other_label][label]
        i.e., other labels incorrectly classified as this label
        """
        fp = {}
        # Get all unique labels from matrix
        all_labels = set()
        for ref_label in self.confusion_matrix:
            all_labels.add(ref_label)
            all_labels.update(self.confusion_matrix[ref_label])

        for label in all_labels:
            fp[label] = 0
            for ref_label in self.confusion_matrix:
                if ref_label != label:
                    fp[label] += self.confusion_matrix.get(ref_label, {}).get(label, 0)
        return fp

    @property
    def false_negatives(self) -> dict[str, int]:
        """Calculate FN for each label from confusion matrix

        FN(label) = sum of all confusion_matrix[label][other_label]
        i.e., this label incorrectly classified as other labels
        """
        fn = {}
        for label in self.confusion_matrix:
            fn[label] = 0
            if label in self.confusion_matrix:
                for hyp_label in self.confusion_matrix[label]:
                    if hyp_label != label:
                        fn[label] += self.confusion_matrix[label][hyp_label]
        return fn


class EpochScorer:
    """NEDC-exact epoch-based scoring

    Implements the epoch scoring algorithm from nedc_eeg_eval_epoch.py
    with consecutive duplicate compression and NULL_CLASS handling.
    """

    def __init__(self, epoch_duration: float = 1.0, null_class: str = "null"):
        """Initialize with epoch parameters

        Args:
            epoch_duration: Duration of each fixed-width epoch (default 1.0)
            null_class: Label for unclassified epochs (default "null")
        """
        self.epoch_duration = epoch_duration
        self.null_class = null_class

    def score(
        self,
        ref_events: list[EventAnnotation],
        hyp_events: list[EventAnnotation],
        file_duration: float,
    ) -> EpochResult:
        """NEDC epoch scoring (sampling midpoints + joint compression).

        Mirrors nedc_eeg_eval_epoch.py:
        - Augment annotations with background to fill gaps (CRITICAL for parity!)
        - Sample at epoch_duration/2, 3/2*epoch_duration, ... <= duration
        - Build substitution matrix at sample resolution
        - Add leading/trailing nulls, jointly compress duplicates
        - Derive per-label hits/misses/false alarms and ins/del from compressed streams
        """
        # CRITICAL: Augment events like NEDC does - fill all gaps with background
        ref_events = self._augment_events(ref_events, file_duration)
        hyp_events = self._augment_events(hyp_events, file_duration)

        # Generate sample times and initialize confusion matrix labels
        samples = self._sample_times(file_duration)
        labels = sorted(
            {ev.label for ev in ref_events} | {ev.label for ev in hyp_events} | {self.null_class}
        )
        confusion: dict[str, dict[str, int]] = {r: {c: 0 for c in labels} for r in labels}

        # Build raw streams with sentinels
        reft: list[str] = [self.null_class]
        hypt: list[str] = [self.null_class]

        for t in samples:
            j = self._time_to_index(t, ref_events)
            k = self._time_to_index(t, hyp_events)
            rlab = ref_events[j].label if j >= 0 else self.null_class
            hlab = hyp_events[k].label if k >= 0 else self.null_class
            confusion[rlab][hlab] += 1
            reft.append(rlab)
            hypt.append(hlab)

        reft.append(self.null_class)
        hypt.append(self.null_class)

        # Jointly compress
        refo, hypo = self._compress_joint(reft, hypt)

        # Per-label counts
        hits: dict[str, int] = {label: 0 for label in labels}
        misses: dict[str, int] = {label: 0 for label in labels}
        false_alarms: dict[str, int] = {label: 0 for label in labels}
        insertions: dict[str, int] = {}
        deletions: dict[str, int] = {}

        for i in range(1, len(refo) - 1):
            rlab, hlab = refo[i], hypo[i]
            if rlab == self.null_class:
                false_alarms[hlab] = false_alarms.get(hlab, 0) + 1
                insertions[hlab] = insertions.get(hlab, 0) + 1
            elif hlab == self.null_class:
                misses[rlab] = misses.get(rlab, 0) + 1
                deletions[rlab] = deletions.get(rlab, 0) + 1
            elif rlab == hlab:
                hits[rlab] = hits.get(rlab, 0) + 1
            else:
                misses[rlab] = misses.get(rlab, 0) + 1
                false_alarms[hlab] = false_alarms.get(hlab, 0) + 1

        return EpochResult(
            confusion_matrix=confusion,
            hits=hits,
            misses=misses,
            false_alarms=false_alarms,
            insertions=insertions,
            deletions=deletions,
            compressed_ref=refo,
            compressed_hyp=hypo,
        )

    def _sample_times(self, file_duration: float) -> list[float]:
        """Generate midpoint sample times per NEDC.

        NEDC uses inclusive boundary: while curr_time <= stop_time
        This is critical for exact parity.
        """
        samples: list[float] = []
        half = self.epoch_duration / 2.0
        i = 0
        while True:
            t = half + i * self.epoch_duration
            # NEDC uses <= for boundary check (inclusive)
            if t > file_duration:
                break
            samples.append(t)
            i += 1
        return samples

    def _time_to_index(self, val: float, events: list[EventAnnotation]) -> int:
        """Return index of event covering time val (inclusive), else -1.

        NEDC uses bitwise & operator: (val >= entry[0]) & (val <= entry[1])
        """
        for idx, ev in enumerate(events):
            # Match NEDC exactly with bitwise & (shouldn't matter but for parity...)
            if (val >= ev.start_time) & (val <= ev.stop_time):
                return idx
        return -1

    def _augment_events(
        self, events: list[EventAnnotation], file_duration: float
    ) -> list[EventAnnotation]:
        """Augment events with background to fill all gaps (NEDC-style).

        NEDC fills gaps between events with background annotation so that
        the entire file duration is covered continuously. This is CRITICAL
        for exact parity - without this, we had a 9 TP difference!
        """
        if not events:
            # If duration is non-positive, return empty to avoid zero-length events
            if file_duration <= 0.0:
                return []
            # Empty annotation - fill entire duration with background
            return [
                EventAnnotation(
                    channel="TERM",
                    start_time=0.0,
                    stop_time=file_duration,
                    label=self.null_class,
                    confidence=1.0,
                )
            ]

        augmented: list[EventAnnotation] = []
        curr_time = 0.0

        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x.start_time)

        for ev in sorted_events:
            # Fill gap before this event if needed
            if curr_time < ev.start_time:
                augmented.append(
                    EventAnnotation(
                        channel="TERM",
                        start_time=curr_time,
                        stop_time=ev.start_time,
                        label=self.null_class,
                        confidence=1.0,
                    )
                )

            # Add the actual event
            augmented.append(ev)
            curr_time = ev.stop_time

        # Fill gap at end if needed
        if curr_time < file_duration:
            augmented.append(
                EventAnnotation(
                    channel="TERM",
                    start_time=curr_time,
                    stop_time=file_duration,
                    label=self.null_class,
                    confidence=1.0,
                )
            )

        return augmented

    def _compress_joint(self, reft: list[str], hypt: list[str]) -> tuple[list[str], list[str]]:
        """Compress duplicate consecutive pairs across ref/hyp jointly."""
        if not reft or not hypt:
            return [], []
        refo = [reft[0]]
        hypo = [hypt[0]]
        for i in range(1, len(reft)):
            if (reft[i] != reft[i - 1]) or (hypt[i] != hypt[i - 1]):
                refo.append(reft[i])
                hypo.append(hypt[i])
        return refo, hypo

    def _create_epochs(self, file_duration: float) -> list[tuple[float, float]]:
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

    def _classify_epochs(
        self, epochs: list[tuple[float, float]], events: list[EventAnnotation]
    ) -> list[str]:
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

    def _compress_epochs(self, labels: list[str]) -> list[str]:
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
        compressed.extend(labels[i] for i in range(1, len(labels)) if labels[i] != labels[i - 1])

        return compressed

    def _compute_metrics(self, ref_compressed: list[str], hyp_compressed: list[str]) -> EpochResult:
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
            ref_label: {hyp_label: 0 for hyp_label in all_labels} for ref_label in all_labels
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
            compressed_hyp=hyp_compressed,
        )
