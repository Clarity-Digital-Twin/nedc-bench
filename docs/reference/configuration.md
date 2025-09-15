# Configuration Reference

## Environment Variables
- `NEDC_NFC` — Path to the NEDC v6.0.0 root. If unset, the API sets it to `nedc_eeg_eval/v6.0.0` relative to the repo.
- `PYTHONPATH` — Automatically prefixed by the API with `<NEDC_NFC>/lib` so the Alpha code can import.
- `REDIS_URL` — Redis connection string for caching (default: `redis://redis:6379`).
- `CACHE_TTL_SECONDS` — Default TTL for cached results (default: `86400`).

## API Settings
- CORS is permissive by default in development (`*`). Adjust in production.
- WebSocket endpoint: `/ws/{job_id}` with `heartbeat` and `ping/pong`.

## Make Targets
- `make dev` — install dev dependencies and pre-commit hooks.
- `make test`, `make test-fast` — run tests with coverage/parallel.
- `make lint`, `make format`, `make typecheck` — code quality.
- `make benchmark` — run benchmarks if present.

## Docker
- API image: `Dockerfile.api` (exposes 8000). Compose and Kubernetes manifests are under `docs/deployment/`.

## Defaults
- Minimum Python: 3.10 (3.11 used in CI for coverage, 3.10–3.11 supported).
