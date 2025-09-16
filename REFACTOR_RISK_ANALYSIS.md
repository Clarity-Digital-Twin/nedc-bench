# 🚨 REFACTOR RISK ANALYSIS: Moving to src/ Structure

**Status**: COMPLETED — IMPLEMENTED IN REPO
**Scope**: Move `nedc_bench/` → `src/nedc_bench/` and `alpha/` → `src/alpha/`
**Risk Level**: LOW–MEDIUM
**Estimated Time**: ~2 hours
**Business Impact**: Minimal with correct packaging; imports remain unchanged

______________________________________________________________________

## Executive Summary

We maintain absolute imports (`import nedc_bench`, `import alpha`) and install the package before tests in CI. Alpha discovers the vendored NEDC via environment variables. Given this, a targeted move of `nedc_bench` into `src/` is safe and small.

Implemented scope:

- Moved `nedc_bench` → `src/nedc_bench`
- Moved `alpha` → `src/alpha`
- Updated Hatch packaging to include both packages from `src/`
- Updated Docker `COPY` step to use `src/`
- Switched Makefile mypy target to `-p nedc_bench`
- Added `pythonpath=["src"]` in pytest config for local dev convenience

______________________________________________________________________

## What actually changes (and what doesn’t)

### Imports

- No import changes for `nedc_bench` users. Absolute imports continue to work once packaging points at `src/`.

### Tests

- CI already installs the package (`uv pip install -e .`), so test discovery remains unchanged.
- For local runs without install, add `pythonpath=["src"]` under `[tool.pytest.ini_options]` (optional quality-of-life).

### Docker

- Change `COPY nedc_bench/` → `COPY src/ ./src/`. Since the package is installed with `-e .`, imports resolve to `nedc_bench` as before. Uvicorn entrypoint (`nedc_bench.api.main:app`) remains valid.

### Alpha wrapper

- Now located at `src/alpha`. It is included in packaging; imports remain `from alpha.wrapper ...`. It still relies on `NEDC_NFC` and `PYTHONPATH` at runtime to locate vendored NEDC.

### CI/CD

- No workflow changes required. Lint, typecheck, tests continue to work post-install.

### Linters / Type checker

- Keep Ruff as-is. For mypy, prefer `mypy -p nedc_bench` (package target) instead of a path.

______________________________________________________________________

## Specific edge cases (low probability in recommended scope)

1. Circular imports

- Moving the package directory alone does not introduce cycles. If future refactors change import structure, re-check.

2. Package data files

- Hatch with `{ include = "nedc_bench", from = "src" }` continues to resolve package resources under `nedc_bench`.

3. Dynamic imports

- `importlib.import_module('nedc_bench.algorithms.X')` remains valid.

4. Subprocess calls

- `python -m nedc_bench.something` still works when the package is installed.

______________________________________________________________________

## Configuration files updated

1. pyproject.toml — point Hatch wheel to `src/nedc_bench`:

```toml
[tool.hatch.build.targets.wheel]
packages = [
  { include = "nedc_bench", from = "src" }
]
```

2. Dockerfile.api — copy `src/`:

```dockerfile
COPY src/ ./src/
```

3. Makefile — use package target for mypy:

```make
mypy -p nedc_bench
```

4. Optional — pytest dev convenience (added):

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

______________________________________________________________________

## Risk matrix (final scope)

| Component    | Risk   | Break Prob. | Fix Difficulty | Fix Time |
| ------------ | ------ | ----------- | -------------- | -------- |
| Imports      | 🟢 Low | ~0%         | Low            | —        |
| Tests        | 🟢 Low | ~0%         | Low            | —        |
| Docker       | 🟡 Med | ~50% (COPY) | Low            | \<30m    |
| CI/CD        | 🟢 Low | ~0%         | Low            | —        |
| Packaging    | 🟡 Med | ~50%        | Low            | \<30m    |
| Linters/Mypy | 🟢 Low | ~0%         | Low            | \<15m    |

______________________________________________________________________

## Post-change validation

- [ ] `uv pip install -e .` installs both `nedc_bench` and `alpha`
- [ ] `make lint typecheck test` passes locally
- [ ] `docker build -f Dockerfile.api .` succeeds

______________________________________________________________________

## Implementation summary (completed)

1. Moved `nedc_bench/` under `src/nedc_bench/` and `alpha/` under `src/alpha/`
1. Updated Hatch packaging to include both from `src`
1. Updated Docker to copy `src/`
1. Switched Makefile mypy to `-p nedc_bench`
1. Added `pythonpath=["src"]` for pytest convenience
1. Adjusted Ruff per-file-ignores to `src/nedc_bench/...` and `src/alpha/...`

______________________________________________________________________

## Success criteria

- [ ] All tests pass
- [ ] Docker builds and API runs
- [ ] Imports remain unchanged (`from nedc_bench...`)
- [ ] CI remains green
- [ ] Linters and mypy pass

______________________________________________________________________

## Alternatives

1. Do nothing now — keep current layout; revisit later.
1. Move both `nedc_bench` and `alpha` under `src/` — higher risk and not necessary now.
1. Add CLI independently — orthogonal to the src move; can be done before or after.

______________________________________________________________________

**Document Version**: 3.0
**Date**: 2025-09-16
**Status**: COMPLETED
