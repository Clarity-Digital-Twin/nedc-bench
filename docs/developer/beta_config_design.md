# Beta Configuration Design Details

This companion document records the first-principles validation performed during
the 2025-10-10 beta configuration work. It captures the agent feedback analysis,
the rationale behind the DP NULL sentinel, and supporting operational details.

## Packaging the Configuration

- **Problem** — Hatch packages only include Python modules by default. Without
  explicit configuration, `beta_params.toml` would be omitted from wheels,
  breaking `importlib.resources`.
- **Fix** — Added the following to `pyproject.toml`:

  ```toml
  [tool.hatch.build.targets.wheel.force-include]
  "src/nedc_bench/config/beta_params.toml" = "nedc_bench/config/beta_params.toml"
  ```

- **Verification** — `python -c "import importlib.resources as r; print(r.files('nedc_bench.config'))"` succeeds on the built package.

## NULL_CLASS Collision Analysis

The DP aligner intentionally retains a local sentinel (`"null"`) instead of
reusing the shared background label (`"bckg"`). The reasoning:

```python
# WRONG (would collide with real data)
from nedc_bench.config.constants import NULL_CLASS  # "bckg"
ref = ["seiz", "bckg", "seiz"]

# DP padding injects additional "bckg" values:
# ["bckg", "seiz", "bckg", "seiz", "bckg"]
# DP can no longer distinguish sentinel padding from genuine labels.
```

By keeping `dp_alignment.NULL_CLASS = "null"`, the algorithm can clearly
identify insertions/deletions during alignment. Other algorithms continue to
import `config.constants.NULL_CLASS = "bckg"`, which reflects actual EEG labels.

See also `docs/algorithms/dp-alignment.md` for maintenance guidance.

## Test Configuration Philosophy

### The Problem

Integration tests that share resources (like NEDC environment setup, job manager state)
require serial execution to avoid race conditions. The pytest-xdist `xdist_group` marker
with `--dist loadgroup` is the **industry-standard solution** for this (per 2025 pytest-xdist docs).

However, the initial implementation placed `--dist=loadgroup` in `pyproject.toml` as a
global default, which **broke test isolation** and caused unexpected behavior.

### Root Cause Analysis

**Initial (Broken) Configuration:**
```toml
# pyproject.toml - WRONG APPROACH
[tool.pytest.ini_options]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--dist=loadgroup",  # ❌ Global default breaks sequential runs
]
```

**Why This Failed:**
- Global `--dist=loadgroup` affects ALL pytest invocations
- Breaks sequential test runs (`pytest` without `-n auto`)
- Developers expect `pytest path/to/test.py` to work normally
- Makes parallel execution mandatory even for single test files

### The Fix: Opt-In Parallel Configuration

**Correct Configuration:**
```toml
# pyproject.toml - Markers and config only
[tool.pytest.ini_options]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    # NOTE: --dist=loadgroup is set in Makefile for parallel runs
    # DO NOT set it here as default - it breaks sequential test runs
]
```

```makefile
# Makefile - Parallel execution policy
test: ## Run all tests with coverage (parallel, fast - default)
	pytest -n auto --dist loadgroup -v --cov=nedc_bench --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	pytest -n auto --dist loadgroup -v
```

### Why This Is Correct

1. **`--dist loadgroup` should be opt-in for parallel runs** - Only activated when running `make test`
2. **Sequential runs work normally** - `pytest path/to/test.py` works as expected
3. **Makefile controls parallel execution policy** - Build system decides when parallelism is appropriate
4. **Developer ergonomics preserved** - No surprises when running individual tests

### Industry Standards (2025)

- `@pytest.mark.xdist_group("group_name")` is the standard way to manage shared resources
- Requires `--dist loadgroup` flag to work (NOT `--dist load` or default distribution)
- Groups are scheduled serially within their group, parallel across different groups
- This is NOT a "paper over" - it's the **proper architectural solution** for shared resource contention

### Test Markers in Use

```python
# tests/test_integration_parity.py
@pytest.mark.xdist_group("nedc_api")
def test_api_integration():
    """Runs serially with other nedc_api group tests when using --dist loadgroup"""
    ...
```

**Groups defined:**
- `nedc_api` - API integration tests requiring job manager
- `nedc_env` - Tests requiring NEDC environment setup
- Other tests run in parallel without restriction

## Agent Feedback Scorecard

Breakdown of the external review (75% accuracy overall):

| Claim | Verdict | Notes |
| --- | --- | --- |
| Beta TOML missing from wheel | ✅ True | Fixed via Hatch `force-include`. |
| DP constants not centralized | ⚠️ Partial | Penalties now centralized; NULL sentinel remains intentionally local. |
| Tests “papered over” | ✅ True | Root issue was configuration; final setup uses industry-standard xdist groups. |

All validated issues have been addressed; intentional design decisions are now
documented for future reference.

## Historical Source

This summary supersedes the relevant sections of
`docs/archive_v2/AGENT_FEEDBACK_VALIDATION_2025.md`.
