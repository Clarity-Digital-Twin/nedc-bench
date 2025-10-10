"""Shared annotation utilities for NEDC-BENCH algorithms

This module provides common functionality for event annotation processing,
particularly the critical background augmentation logic used across multiple
scoring algorithms.
"""

from __future__ import annotations

from nedc_bench.models.annotations import EventAnnotation

# Default channel name used for background/null events
DEFAULT_CHANNEL = "TERM"


def fill_gaps_with_background(
    events: list[EventAnnotation],
    file_duration: float,
    null_label: str,
    channel: str = DEFAULT_CHANNEL,
) -> list[EventAnnotation]:
    """Fill gaps between events with background annotation to cover full duration.

    This is CRITICAL for NEDC parity. The NEDC tooling fills all gaps with
    background events so that the entire file duration [0, file_duration] is
    covered continuously. Without this augmentation, scoring results will differ
    significantly.

    Args:
        events: List of event annotations (may be empty or have gaps)
        file_duration: Total duration of the file to cover
        null_label: Label to use for background/null events (e.g., "null", "bckg")
        channel: Channel name for background events (default: "TERM")

    Returns:
        Augmented list of events covering [0, file_duration] with no gaps

    Examples:
        >>> events = [EventAnnotation("ch1", 1.0, 2.0, "seizure", 1.0)]
        >>> augmented = fill_gaps_with_background(events, 5.0, "null")
        >>> # Returns: [null(0-1), seizure(1-2), null(2-5)]
    """
    # Handle empty events - fill entire duration with background
    if not events:
        # If duration is non-positive, return empty to avoid zero-length events
        if file_duration <= 0.0:
            return []
        return [
            EventAnnotation(
                channel=channel,
                start_time=0.0,
                stop_time=file_duration,
                label=null_label,
                confidence=1.0,
            )
        ]

    # Sort events by start time
    sorted_events = sorted(events, key=lambda e: e.start_time)

    augmented: list[EventAnnotation] = []
    current_time = 0.0

    for event in sorted_events:
        # Fill gap before this event if needed
        if current_time < event.start_time:
            augmented.append(
                EventAnnotation(
                    channel=channel,
                    start_time=current_time,
                    stop_time=event.start_time,
                    label=null_label,
                    confidence=1.0,
                )
            )

        # Add the actual event
        augmented.append(event)
        current_time = event.stop_time

    # Fill gap at end if needed
    if current_time < file_duration:
        augmented.append(
            EventAnnotation(
                channel=channel,
                start_time=current_time,
                stop_time=file_duration,
                label=null_label,
                confidence=1.0,
            )
        )

    return augmented
