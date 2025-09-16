# Frequently Asked Questions

## What Python versions are supported?

- Minimum Python is 3.10. CI runs on 3.10 and 3.11. The package metadata declares 3.10–3.12 classifiers.

## Where is the CLI?

- A standalone CLI is not implemented yet. Use the API (`/api/v1/*`) or scripts in `scripts/` (see `docs/reference/cli.md`).

## How do I run the API?

- `uv run uvicorn nedc_bench.api.main:app --reload` and open `http://localhost:8000/docs` for the OpenAPI UI. See `docs/api/` for endpoints and examples.

## Why does `/api/v1/ready` return 503 locally?

- The readiness probe requires the background worker to be running and Redis reachable. In dev, absence of Redis will cause 503 (health at `/api/v1/health` still returns 200).

## Where do I set `NEDC_NFC` and `PYTHONPATH`?

- The API sets these automatically to the bundled `nedc_eeg_eval/v6.0.0` in development. For scripts, export them manually if needed.

## How do I validate parity with NEDC?

- Run `uv run python scripts/compare_parity.py`. It compares Alpha and Beta outputs and fails if mismatches exceed tolerances.
