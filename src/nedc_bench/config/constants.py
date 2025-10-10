"""Beta pipeline configuration constants.

Centralized constants for NEDC algorithm parameters.
These values are derived from NEDC reference implementation but packaged
independently for beta-only deployments.

Separation of Concerns:
- Algorithm constants = Scientific correctness (THIS MODULE)
  - epoch_duration, null_class, DP penalties
  - These affect NEDC parity and must match published methodology
  - Version-controlled with algorithms

- API constants = Infrastructure (kept in API modules)
  - max_file_size, timeouts, worker counts
  - These are operational concerns, better as env vars or API config
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Re-export DEFAULT_CHANNEL from annotations.py (don't duplicate!)
# This constant was already defined and should be reused
from nedc_bench.utils.annotations import DEFAULT_CHANNEL

__all__ = [
    "DEFAULT_CHANNEL",
    "DEFAULT_LABEL_MAP",
    "DP_PENALTY_DEL",
    "DP_PENALTY_INS",
    "DP_PENALTY_SUB",
    "EPOCH_DURATION",
    "MIN_PRECISION",
    "NULL_CLASS",
    "OVERLAP_GUARD_WIDTH",
    "LabelMap",
]


# ============================================================================
# NEDC Algorithm Parameters
# ============================================================================

# Epoch-based scoring parameters
EPOCH_DURATION: Final[float] = 0.25
"""Duration of fixed-width epochs in seconds (NEDC standard)"""

NULL_CLASS: Final[str] = "bckg"
"""Label for unclassified/background epochs (lowercase canonical form)

Note: NEDC TOML uses uppercase "BCKG" but params loader normalizes to lowercase.
The canonical form used throughout beta pipeline is "bckg" (lowercase).
"""

# Dynamic Programming (DP) alignment penalties
DP_PENALTY_DEL: Final[float] = 1.0
"""Penalty for deletions in DP alignment"""

DP_PENALTY_INS: Final[float] = 1.0
"""Penalty for insertions in DP alignment"""

DP_PENALTY_SUB: Final[float] = 1.0
"""Penalty for substitutions in DP alignment"""

# Overlap-based scoring parameters
OVERLAP_GUARD_WIDTH: Final[float] = 0.001
"""Small epsilon for boundary handling in overlap scoring (seconds)"""

# Precision for time rounding (NEDC standard)
MIN_PRECISION: Final[int] = 4
"""Minimum decimal precision for time values (digits after decimal point)"""


# ============================================================================
# Label Mappings
# ============================================================================


@dataclass(frozen=True)
class LabelMap:
    """Default two-class label mapping (seiz vs bckg).

    All labels are stored in lowercase canonical form, matching params.py normalization.

    Attributes:
        seiz: Tuple of seizure-related labels
        bckg: Tuple of background-related labels
    """

    seiz: tuple[str, ...] = ("seiz",)
    bckg: tuple[str, ...] = ("bckg",)

    def to_dict(self) -> dict[str, str]:
        """Flatten to raw_label -> class mapping.

        Returns:
            Dictionary mapping each raw label to its class (all lowercase)

        Example:
            >>> label_map = LabelMap()
            >>> label_map.to_dict()
            {'seiz': 'seiz', 'bckg': 'bckg'}
        """
        mapping: dict[str, str] = {}
        for cls in ("seiz", "bckg"):
            labels = getattr(self, cls)
            for label in labels:
                mapping[label.lower()] = cls.lower()
        return mapping


DEFAULT_LABEL_MAP: Final[LabelMap] = LabelMap()
"""Default two-class label mapping for seizure detection (seiz vs bckg)"""
