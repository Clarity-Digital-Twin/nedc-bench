"""NEDC-BENCH: Modern benchmarking platform for EEG event detection systems."""

__version__ = "0.1.0"
__author__ = "Clarity Digital Twin"
__license__ = "Apache-2.0"

from typing import Final

# Package metadata
PACKAGE_NAME: Final[str] = "nedc-bench"
PACKAGE_VERSION: Final[str] = __version__

# Re-export main components when they're ready
__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "PACKAGE_NAME",
    "PACKAGE_VERSION",
]