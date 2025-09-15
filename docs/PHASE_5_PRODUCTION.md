# Phase 5: Production — Performance, Observability, and Deployment (Consolidated)

This document replaces previous Phase 5 drafts. It is aligned with the current codebase and is immediately implementable without introducing new microservices. It defines exactly what to ship in 5 days for a production‑ready, observable platform.

## Scope and Principles

- Single service architecture: the FastAPI app (this repo) runs the Beta algorithms in‑process.
- Redis provides result caching. Do not introduce a separate Beta service.
- Alpha container is CI‑only for parity validation; do not run Alpha in production.
- Endpoints are consistent with the repo: `/api/v1/health` exists; add `/api/v1/ready` and expose `/metrics`.
- Keep type checking and linting strict; no hacks. Preserve algorithmic parity.

## Success Criteria (TDD)

- Docker Compose stack up and healthy.
- Kubernetes manifests validated (probes pass).
- Prometheus metrics exposed and scrapeable; basic dashboards available.
- Caching reduces warm‑path latency by ≥10x on typical inputs (no parity drift).
- Production documentation and runbook complete and accurate.

## Deliverables

- `docker-compose.yml`: api, redis (redis:7-alpine), prometheus (prom/prometheus:latest), optional grafana (grafana/grafana:latest).
- `Dockerfile.api`: slim or multi‑stage image; target < ~200MB.
- `k8s/`: minimal API `deployment.yaml` and `service.yaml` (HPA optional).
- `monitoring/prometheus.yml`: scrape config for the API.
- `docs/runbook.md`: operations guide (deploy, monitor, scale, troubleshoot).
- `docs/deployment.md`: deployment instructions and configuration matrix.

## Architecture

- API (FastAPI) exposes evaluation endpoints and WebSockets; orchestrates Beta algorithms locally.
- Redis provides caching for evaluation results.
- Prometheus scrapes `/metrics` from the API container; Grafana is optional.
- Kubernetes runs the API with liveness/readiness probes, resource limits, and optional autoscaling.

## Day 1 — Docker and Compose

1) Optimize `Dockerfile.api` (multi‑stage or slim)

- Base: `python:3.11-slim`.
- Install build tools only in the builder stage; copy only needed artifacts to final.
- Keep env consistent with repo: `NEDC_NFC=/app/nedc_eeg_eval/v6.0.0`.
- Run as non‑root user; expose `8000`.

2) Compose stack (api, redis, prometheus, grafana)

```yaml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - NEDC_NFC=/app/nedc_eeg_eval/v6.0.0
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    restart: unless-stopped
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis_data:
  grafana_data:
```

## Day 2 — Performance (Caching and Concurrency)

1) Redis cache (async, typed)

- Implement `RedisCache` (using `redis.asyncio`) with JSON get/set and TTL (e.g., 24h).
- Key scheme: `sha256(ref|hyp|algorithms|version)` for correctness.
- Integrate at orchestrator boundary: on cache hit → return; on miss → compute and store.

2) Concurrency (safe and bounded)

- For batch evaluations, add a `ParallelEvaluator` using `ProcessPoolExecutor` for CPU‑bound tasks, capped at `cpu_count()`.
- Do not parallelize internals in a way that alters ordering or floating rounding; keep parity strict.

## Day 3 — Monitoring & Metrics

1) Instrumentation

- Add `monitoring/metrics.py` with:
  - `nedc_evaluations_total{algorithm,pipeline,status}` (Counter)
  - `nedc_evaluation_duration_seconds{algorithm,pipeline}` (Histogram; buckets [0.1, 0.5, 1, 2.5, 5, 10])
  - `nedc_parity_failures_total{algorithm}` (Counter)
  - `nedc_active_evaluations` (Gauge)
- Decorate orchestration entry points with a `track_evaluation` decorator.
- Add `/metrics` endpoint exposing `prometheus_client.generate_latest` as `text/plain`.

2) Prometheus scrape config

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'nedc-bench-api'
    static_configs:
      - targets: ['api:8000']
```

## Day 4 — Kubernetes (API only)

- Create `k8s/deployment.yaml` and `k8s/service.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nedc-bench-api
  labels:
    app: nedc-bench
    component: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nedc-bench
      component: api
  template:
    metadata:
      labels:
        app: nedc-bench
        component: api
    spec:
      containers:
        - name: api
          image: nedc-bench/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: NEDC_NFC
              value: "/app/nedc_eeg_eval/v6.0.0"
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /api/v1/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v1/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nedc-bench-api
  labels:
    app: nedc-bench
    component: api
spec:
  selector:
    app: nedc-bench
    component: api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

- Optional HPA (in cluster): min 2, max 10, target CPU 70%.
- Use official charts for Redis/Prometheus/Grafana in production clusters; keep only API manifests in this repo.

## Day 5 — Production Readiness & Docs

1) Health and readiness

- Ensure `/api/v1/health` returns 200.
- Implement `/api/v1/ready` to verify Redis connectivity and internal worker readiness.

2) Integration tests (mark as integration)

- Health/Ready/Metrics endpoints return 200.
- Caching test shows warm path ≥10x faster than cold path.
- Rate limiting test verifies 429s under sustained bursts.

3) Documentation

- `docs/runbook.md`:
  - Docker Compose: up, logs, metrics, troubleshooting, graceful shutdown.
  - Kubernetes: apply, check probes, scale, rollback.
  - Monitoring: key metrics and alert thresholds.
- `docs/deployment.md`:
  - Build/tag/push instructions; environment variables; configuration matrix.

## Definition of Done

- `docker-compose up -d` brings up api/redis/prometheus (and grafana if enabled); API healthcheck is green.
- `/metrics` exposes counters, histogram, and gauge; Prometheus scrapes successfully.
- K8s manifests pass probes and serve traffic; HPA scales under synthetic load (optional).
- Caching demonstrates measurable speedup without parity changes.
- Documentation is complete and accurate.

## Notes and Constraints

- Keep `/api/v1/health` and `/api/v1/ready` paths aligned with the existing router.
- Do not introduce a `beta` microservice; the Beta algorithms live inside this API.
- Alpha is CI‑only for parity; do not deploy Alpha to production.
- Maintain mypy strict and ruff clean; restrict per‑file ignores to narrow, justified cases.

---

### Appendix: Metrics Decorator (reference)

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from typing import Callable, Awaitable

evaluation_counter = Counter(
    'nedc_evaluations_total', 'Total number of evaluations', ['algorithm', 'pipeline', 'status']
)
evaluation_duration = Histogram(
    'nedc_evaluation_duration_seconds', 'Evaluation duration (s)', ['algorithm', 'pipeline'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)
parity_failures = Counter('nedc_parity_failures_total', 'Total parity failures', ['algorithm'])
active_evaluations = Gauge('nedc_active_evaluations', 'Currently running evaluations')

def track_evaluation(algorithm: str, pipeline: str) -> Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]:
    def decorator(func: Callable[..., Awaitable]):
        async def wrapper(*args, **kwargs):
            active_evaluations.inc()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                evaluation_counter.labels(algorithm=algorithm, pipeline=pipeline, status='success').inc()
                return result
            except Exception:
                evaluation_counter.labels(algorithm=algorithm, pipeline=pipeline, status='error').inc()
                raise
            finally:
                evaluation_duration.labels(algorithm=algorithm, pipeline=pipeline).observe(time.time() - start)
                active_evaluations.dec()
        return wrapper
    return decorator
```

### Appendix: Prometheus Config (reference)

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: nedc-bench-api
    static_configs:
      - targets: ['api:8000']
```

