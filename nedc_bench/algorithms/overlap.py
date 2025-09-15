"""Overlap Scoring algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Overlap detection separate from counting
- Open/Closed: Extensible overlap conditions
- Liskov Substitution: Consistent result interface
- Interface Segregation: Minimal focused methods
- Dependency Inversion: Depend on EventAnnotation abstraction
"""

from dataclasses import dataclass

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class OverlapResult:
    """NEDC overlap results - NO confusion matrix!

    Per NEDC line 686: "overlap method does not give us a confusion matrix"
    All counts are integers per NEDC source lines 596-613.
    """

    # Direct counts (all integers per NEDC)
    hits: dict[str, int]  # Per-label hits
    misses: dict[str, int]  # Per-label misses
    false_alarms: dict[str, int]  # Per-label false alarms

    # NEDC mappings (lines 711-713)
    insertions: dict[str, int]  # = false_alarms
    deletions: dict[str, int]  # = misses

    # Totals
    total_hits: int
    total_misses: int
    total_false_alarms: int


class OverlapScorer:
    """NEDC-exact overlap scoring (ANY overlap, not proportional)

    Implements the overlap scoring algorithm from nedc_eeg_eval_ovlp.py
    using binary ANY overlap detection, not proportional overlap.
    """

    def score(
        self, ref_events: list[EventAnnotation], hyp_events: list[EventAnnotation]
    ) -> OverlapResult:
        """NEDC overlap: binary ANY overlap detection

        Implements NEDC lines 593-613: ANY temporal overlap counts as hit.

        Args:
            ref_events: Reference event annotations
            hyp_events: Hypothesis event annotations

        Returns:
            OverlapResult with integer counts and NEDC mappings
        """
        per_label_hits = {}
        per_label_misses = {}
        per_label_false_alarms = {}

        # Check each ref event (NEDC lines 593-601)
        for ref_event in ref_events:
            label = ref_event.label
            has_overlap = False

            for hyp_event in hyp_events:
                # NEDC overlap condition (line 652): ANY overlap
                # (event[1] > start) and (event[0] < stop)
                if (
                    hyp_event.stop_time > ref_event.start_time
                    and hyp_event.start_time < ref_event.stop_time
                    and hyp_event.label == label
                ):
                    has_overlap = True
                    break

            # Initialize counters if needed
            if label not in per_label_hits:
                per_label_hits[label] = 0
                per_label_misses[label] = 0

            # Count hit or miss
            if has_overlap:
                per_label_hits[label] += 1  # INTEGER increment
            else:
                per_label_misses[label] += 1  # INTEGER increment

        # Check each hyp for false alarms (lines 603-609)
        for hyp_event in hyp_events:
            label = hyp_event.label
            has_overlap = False

            for ref_event in ref_events:
                # Same overlap condition, checking if hyp matches any ref
                if (
                    hyp_event.stop_time > ref_event.start_time
                    and hyp_event.start_time < ref_event.stop_time
                    and ref_event.label == label
                ):
                    has_overlap = True
                    break

            # Count false alarm if no overlap found
            if not has_overlap:
                if label not in per_label_false_alarms:
                    per_label_false_alarms[label] = 0
                per_label_false_alarms[label] += 1  # INTEGER increment

        # NEDC mappings (lines 711-713)
        # Line 712: insertions = false_alarms
        # Line 713: deletions = misses
        return OverlapResult(
            hits=per_label_hits,
            misses=per_label_misses,
            false_alarms=per_label_false_alarms,
            insertions=per_label_false_alarms.copy(),  # Line 712
            deletions=per_label_misses.copy(),  # Line 713
            total_hits=sum(per_label_hits.values()),
            total_misses=sum(per_label_misses.values()),
            total_false_alarms=sum(per_label_false_alarms.values()),
        )
