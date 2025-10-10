"""Utilities to load NEDC parameters and label mappings.

Priority-based loading strategy:
1. BETA_CONFIG_PATH environment variable (custom user config)
2. Bundled beta_params.toml (shipped with package)
3. NEDC_NFC environment (dual pipeline backwards compat)
4. In-repo NEDC TOML (development)
5. Hardcoded defaults (last resort)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # Python 3.11+
    import tomllib as _tomllib  # type: ignore[import-not-found]
except ImportError:  # Python 3.10 fallback
    import tomli as _tomllib

# Python 3.10+ compatible resource loading
try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources  # type: ignore[import-not-found]

from nedc_bench.config.constants import (
    DEFAULT_LABEL_MAP,
    EPOCH_DURATION,
    NULL_CLASS,
    OVERLAP_GUARD_WIDTH,
)

PARAM_REL_PATH = "src/nedc_eeg_eval/nedc_eeg_eval_params_v00.toml"


@dataclass
class NedcParams:
    """Container for NEDC parameters used in scoring."""

    label_map: dict[str, str]  # raw_label(lower) -> class(lower)
    epoch_duration: float
    null_class: str
    guard_width: float


def _default_param_path() -> Path:
    """Return fallback param path inside the repo."""
    return Path("nedc_eeg_eval/v6.0.0") / PARAM_REL_PATH


def _env_param_path() -> Path | None:
    """Return path based on NEDC_NFC env if available."""
    root = os.environ.get("NEDC_NFC")
    if not root:
        return None
    return Path(root) / PARAM_REL_PATH


def _beta_config_path() -> Path | None:
    """Return custom beta config path from environment if set."""
    custom = os.environ.get("BETA_CONFIG_PATH")
    if not custom:
        return None
    return Path(custom)


def _load_from_beta_toml(path: Path) -> NedcParams:
    """Load parameters from beta_params.toml format.

    Beta TOML format uses lowercase canonical labels and nested structure:
    [label_map]
    seiz = ["seiz"]
    bckg = ["bckg"]

    [algorithms.epoch]
    duration = 0.25
    null_class = "bckg"

    [algorithms.overlap]
    guard_width = 0.001

    Args:
        path: Path to beta_params.toml file or file-like object

    Returns:
        NedcParams with lowercase mapping and numeric params
    """
    # Handle both Path and Traversable (from importlib.resources)
    if hasattr(path, "read_bytes"):
        data = _tomllib.loads(path.read_bytes().decode("utf-8"))  # type: ignore[union-attr]
    else:
        with open(path, "rb") as fp:
            data = _tomllib.load(fp)

    # Load label map (already lowercase in beta format)
    label_map_raw = data.get("label_map", {})
    label_map: dict[str, str] = {}
    for cls, labels in label_map_raw.items():
        # labels is a list in beta format
        for lab in labels:
            label_map[lab.lower()] = cls.lower()

    # Algorithm params (nested structure)
    epoch_data = data.get("algorithms", {}).get("epoch", {})
    epoch_duration = float(epoch_data.get("duration", 0.25))
    null_class = str(epoch_data.get("null_class", "bckg")).lower()

    overlap_data = data.get("algorithms", {}).get("overlap", {})
    guard_width = float(overlap_data.get("guard_width", 0.001))

    return NedcParams(
        label_map=label_map,
        epoch_duration=epoch_duration,
        null_class=null_class,
        guard_width=guard_width,
    )


def _load_from_nedc_toml(path: Path) -> NedcParams:
    """Load parameters from NEDC TOML format.

    NEDC TOML format uses uppercase labels and flat structure:
    [MAP]
    SEIZ = "SEIZ"
    BCKG = "BCKG"

    [NEDC_EPOCH]
    epoch_duration = '0.25'
    null_class = "BCKG"

    Args:
        path: Path to NEDC TOML file

    Returns:
        NedcParams with lowercase mapping and numeric params
    """
    with path.open("rb") as fp:
        data = _tomllib.load(fp)

    # Load label map and normalize to lowercase
    label_map_raw = data.get("MAP", {})
    # Inverted map: raw label -> class
    label_map: dict[str, str] = {}
    for cls, labels in label_map_raw.items():
        # labels may be a string (comma-separated) or single string
        if isinstance(labels, str):
            parts = [s.strip() for s in labels.split(",") if s.strip()]
        else:
            parts = []
        for lab in parts or [labels]:
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


def _default_params() -> NedcParams:
    """Return hardcoded fallback params from constants (last resort).

    Uses centralized constants to ensure consistency across the codebase.

    Returns:
        NedcParams with NEDC-compatible defaults from constants.py
    """
    return NedcParams(
        label_map=DEFAULT_LABEL_MAP.to_dict(),
        epoch_duration=EPOCH_DURATION,
        null_class=NULL_CLASS,
        guard_width=OVERLAP_GUARD_WIDTH,
    )


def load_nedc_params() -> NedcParams:
    """Load parameters and label map from TOML.

    Priority-based loading cascade:
    1. BETA_CONFIG_PATH env → custom user config
    2. Bundled beta_params.toml → default beta config (shipped with package)
    3. NEDC_NFC env → dual pipeline (backwards compatible)
    4. In-repo NEDC → development mode
    5. Hardcoded defaults → last resort

    Returns:
        NedcParams with lowercase mapping and numeric params.
    """
    # Try 1: Custom beta config from environment
    custom_beta = _beta_config_path()
    if custom_beta and custom_beta.exists():
        return _load_from_beta_toml(custom_beta)

    # Try 2: Bundled beta config (shipped with package)
    try:
        # Python 3.10+ compatible resource loading
        if hasattr(resources, "files"):
            beta_config = resources.files("nedc_bench.config") / "beta_params.toml"
            if beta_config.is_file():  # type: ignore[union-attr]
                return _load_from_beta_toml(beta_config)  # type: ignore[arg-type]
    except (ImportError, FileNotFoundError, AttributeError):
        pass

    # Try 3: NEDC_NFC environment (dual pipeline backwards compat)
    nedc_env = _env_param_path()
    if nedc_env and nedc_env.exists():
        return _load_from_nedc_toml(nedc_env)

    # Try 4: In-repo NEDC (development mode)
    nedc_repo = _default_param_path()
    if nedc_repo.exists():
        return _load_from_nedc_toml(nedc_repo)

    # Fallback 5: Hardcoded defaults (last resort)
    return _default_params()


def map_event_label(label: str, mapping: dict[str, str]) -> str:
    """Map a raw event label to its class using provided mapping.

    Falls back to lowercased original label if not present in mapping.
    """
    low = label.lower()
    return mapping.get(low, low)
