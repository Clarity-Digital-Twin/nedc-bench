"""Utilities to load NEDC parameters and label mappings.

Tries to read from the NEDC installation (env NEDC_NFC),
falls back to the in-repo param file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


try:  # Python 3.11+
    import tomllib as _tomllib  # type: ignore[attr-defined]
except Exception:  # Python 3.10 fallback
    import tomli as _tomllib  # type: ignore[no-redef]


PARAM_REL_PATH = "src/nedc_eeg_eval/nedc_eeg_eval_params_v00.toml"


@dataclass
class NedcParams:
    """Container for NEDC parameters used in scoring."""

    label_map: Dict[str, str]  # raw_label(lower) -> class(lower)
    epoch_duration: float
    null_class: str
    guard_width: float


def _default_param_path() -> Path:
    """Return fallback param path inside the repo."""
    return Path("nedc_eeg_eval/v6.0.0") / PARAM_REL_PATH


def _env_param_path() -> Path | None:
    """Return path based on NEDC_NFC env if available."""
    import os

    root = os.environ.get("NEDC_NFC")
    if not root:
        return None
    return Path(root) / PARAM_REL_PATH


def load_nedc_params() -> NedcParams:
    """Load parameters and label map from TOML.

    Returns:
        NedcParams with lowercase mapping and numeric params.
    """
    p = _env_param_path()
    if p is None or not p.exists():
        p = _default_param_path()

    with open(p, "rb") as fp:
        data = _tomllib.load(fp)

    # Load label map and normalize to lowercase
    label_map_raw = data.get("MAP", {})
    # Inverted map: raw label -> class
    label_map: Dict[str, str] = {}
    for cls, labels in label_map_raw.items():
        # labels may be a string (comma-separated) or single string
        if isinstance(labels, str):
            parts = [s.strip() for s in labels.split(",") if s.strip()]
        else:
            parts = []
        for lab in parts if parts else [labels]:
            if isinstance(lab, str):
                label_map[lab.lower()] = cls.lower()

    # Epoch params
    ep = data.get("NEDC_EPOCH", {})
    epoch_duration = float(str(ep.get("epoch_duration", "0.25")).strip("'\""))
    null_class = str(ep.get("null_class", "BCKG")).strip("'\"").lower()

    # Overlap params
    ov = data.get("NEDC_OVERLAP", {})
    guard_width = float(str(ov.get("guard_width", "0.001")).strip("'\""))

    return NedcParams(
        label_map=label_map,
        epoch_duration=epoch_duration,
        null_class=null_class,
        guard_width=guard_width,
    )


def map_event_label(label: str, mapping: Dict[str, str]) -> str:
    """Map a raw event label to its class using provided mapping.

    Falls back to lowercased original label if not present in mapping.
    """
    low = label.lower()
    return mapping.get(low, low)
