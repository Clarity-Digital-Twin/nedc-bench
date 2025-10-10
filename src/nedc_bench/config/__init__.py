"""Beta pipeline configuration package.

This package contains:
- beta_params.toml: Bundled NEDC-compatible parameters for beta-only deployments
- constants.py: Type-safe Python constants derived from beta_params.toml

The beta config eliminates dependency on nedc_eeg_eval/ directory while maintaining
full NEDC parity and backwards compatibility with dual pipeline.
"""

__all__ = ["beta_params.toml", "constants"]
