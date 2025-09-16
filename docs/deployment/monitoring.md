# Monitoring Guide

## Metrics

### Prometheus

- Endpoint: `GET /metrics` (text format)
- Scrape interval: 15–30s typical
- Useful series:
  - Request latency histograms (uvicorn/http)
  - Evaluation duration per algorithm
  - Active evaluations gauge

Multi-worker metrics:

- If running with `MAX_WORKERS > 1`, enable Prometheus multiprocess mode by setting `PROMETHEUS_MULTIPROC_DIR`.
- The image entrypoint creates/cleans the directory and the API exposes multiprocess metrics when this env var is set.

Example:

```bash
curl http://localhost:8000/metrics
```

## Logging

- API uses Python `logging` with level INFO by default.
- Increase verbosity when running uvicorn:
  ```bash
  uv run uvicorn nedc_bench.api.main:app --log-level debug
  ```

## Health Checks

- Liveness: `GET /api/v1/health` (process up)
- Readiness: `GET /api/v1/ready` (worker + Redis reachable)

## Dashboards

- Grafana panels: latency P50/P95, throughput, parity failures, active jobs.
- Prometheus scrape: create a ServiceMonitor targeting the API Service.

## Alerts

- Alert on high error rate, readiness failures, elevated latency, parity failures.

## Related

- [Configuration](configuration.md)
- [Scaling](scaling.md)
- [Troubleshooting](troubleshooting.md)
