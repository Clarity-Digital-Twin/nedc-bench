# Migration Plan: Move to src/ Layout (Low-Risk Scope)

This plan migrates both `nedc_bench/` to `src/nedc_bench/` and `alpha/` to `src/alpha/`. `nedc_eeg_eval/` remains at repo root. Imports stay the same, CI remains unchanged, and Docker needs a small COPY tweak.

## Target Structure

```
nedc-bench/
├── nedc_eeg_eval/         # STAYS AT ROOT (vendored, untouched)
├── src/
│   ├── nedc_bench/        # Our package (moved)
│       ├── algorithms/
│       ├── api/
│       ├── models/
│       ├── orchestration/
│       ├── utils/
│       └── validation/
│   └── alpha/             # Alpha wrapper (moved)
├── tests/
├── scripts/
└── pyproject.toml         # Updated Hatch wheel target
```

## Preconditions

- `make lint typecheck test` passes on main
- `docker build -f Dockerfile.api .` succeeds

## Step-by-step

1. Move code

```bash
mkdir -p src
git mv nedc_bench src/
git mv alpha src/
```

2. Update packaging (Hatch)

Edit `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = [
  { include = "nedc_bench", from = "src" },
  { include = "alpha", from = "src" }
]

[tool.hatch.version]
path = "src/nedc_bench/__init__.py"
```

3. Update Dockerfile.api

Change the application copy step:

```dockerfile
- COPY nedc_bench/ ./nedc_bench/
+ COPY src/ ./src/
  COPY nedc_eeg_eval/ ./nedc_eeg_eval/
  COPY alpha/ ./alpha/
```

No change to entrypoint. The package is installed with `-e .[api]` so `nedc_bench` is importable.

4. Update Makefile (mypy target)

Prefer the package target to path sensitivity:

```make
- mypy nedc_bench/
+ mypy -p nedc_bench
```

5. Optional (local dev convenience)

Allow `pytest` without install by adding to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

## Validation

```bash
uv pip install -e .
make lint
make typecheck
make test

docker build -f Dockerfile.api .
```

## Rollback

```bash
git mv src/nedc_bench ./
git checkout -- pyproject.toml Dockerfile.api Makefile
```

## Notes

- `alpha/` remains at repo root; no path changes needed because Alpha uses env (`NEDC_NFC`, `PYTHONPATH`).
- Imports remain absolute and unchanged (`from nedc_bench...`).
- CI workflows require no changes (they already do `uv pip install -e .`).

## Phase 2 (Optional, later): Move `alpha/`

If/when desired:

- Move `alpha/` → `src/alpha/`
- Either package `alpha` too (add `{ include = "alpha", from = "src" }`) or export `PYTHONPATH=src` in Docker and dev environments
- Update Docker copy to include `src/`

Keep this separate from the `nedc_bench` move to minimize risk.
