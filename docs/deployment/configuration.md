# Configuration Guide

## Environment Variables

### Core
- `NEDC_NFC` — Path to the NEDC v6.0.0 root (API sets a default to `nedc_eeg_eval/v6.0.0`).
- `PYTHONPATH` — API prefixes this with `<NEDC_NFC>/lib` for Alpha imports.

### API
- Host/port are set by uvicorn: `uvicorn ... --host 0.0.0.0 --port 8000`.
- CORS is permissive in development; tighten for production.

### Redis Cache
- `REDIS_URL` — Default `redis://redis:6379` (see docker-compose).
- `CACHE_TTL_SECONDS` — Default `86400`.

## Files and Tools
- `pyproject.toml` — Tooling config (ruff, mypy, pytest, coverage), `requires-python >=3.10`.
- `Makefile` — Common commands (`make dev`, `make test`, `make lint`).
- `docker-compose.yml` — Local stack (API + Redis + Prometheus), if present.

## Pipelines
- Alpha: Original NEDC tool executed via wrapper; requires `NEDC_NFC` and `PYTHONPATH`.
- Beta: Native Python implementations under `nedc_bench/algorithms/`.

## Performance
- Increase uvicorn workers for CPU-bound concurrency: `uvicorn ... --workers 4`.
- Use Redis to cache repeated evaluations.

## Monitoring
- Prometheus scrapes `/metrics` (text format). Add ServiceMonitor in Kubernetes.

## Related
- [Docker Deployment](docker.md)
- [Environment Variables Reference](../reference/configuration.md)
- [Troubleshooting](troubleshooting.md)
