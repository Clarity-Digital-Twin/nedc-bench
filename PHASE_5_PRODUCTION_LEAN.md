# Phase 5: Production Deployment (Lean Version)
## Goal: Ship a Production-Ready System with Essential Features

### Duration: 3 Days

### Core Principle: "Make it work, make it right, make it fast"

---

## Day 1: Dockerize Everything

### Morning: Create Production Dockerfiles

#### 1. Alpha Pipeline Docker (with legacy NEDC)
```dockerfile
# Dockerfile.alpha
FROM python:3.11-slim

# Install NEDC dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy NEDC tool
COPY nedc_eeg_eval /opt/nedc_eeg_eval
COPY alpha /app/alpha

WORKDIR /app

# Install Python deps
COPY requirements/alpha.txt .
RUN pip install --no-cache-dir -r alpha.txt

# Set NEDC environment
ENV NEDC_NFC=/opt/nedc_eeg_eval/v6.0.0
ENV PYTHONPATH=/opt/nedc_eeg_eval/v6.0.0/lib:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import nedc_eeg_eval" || exit 1

CMD ["python", "-m", "alpha.wrapper.api"]
```

#### 2. Beta Pipeline Docker (pure Python)
```dockerfile
# Dockerfile.beta
FROM python:3.11-slim

WORKDIR /app

# Copy only Beta code
COPY nedc_bench /app/nedc_bench
COPY requirements/beta.txt .

RUN pip install --no-cache-dir -r beta.txt

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "nedc_bench.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Afternoon: Docker Compose Stack
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Redis for caching results
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Alpha pipeline (NEDC wrapper)
  alpha:
    build:
      context: .
      dockerfile: Dockerfile.alpha
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/data:ro
      - ./output:/output
    depends_on:
      - redis

  # Beta pipeline (Python reimplementation)
  beta:
    build:
      context: .
      dockerfile: Dockerfile.beta
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/data:ro
      - ./output:/output
    depends_on:
      - redis

  # Main API that orchestrates both pipelines
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ALPHA_URL=http://alpha:8080
      - BETA_URL=http://beta:8001
      - REDIS_URL=redis://redis:6379
    depends_on:
      - alpha
      - beta
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s

  # Simple Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  redis_data:
  prometheus_data:
```

---

## Day 2: API with Caching & Performance

### Morning: FastAPI with Redis Cache

```python
# nedc_bench/api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
import redis
import json
import hashlib
import time
from typing import List, Optional

app = FastAPI(title="NEDC Bench API", version="1.0.0")

# Metrics
evaluation_counter = Counter(
    'nedc_evaluations_total',
    'Total evaluations',
    ['algorithm', 'pipeline', 'status']
)

evaluation_duration = Histogram(
    'nedc_evaluation_duration_seconds',
    'Evaluation duration',
    ['algorithm', 'pipeline']
)

# Redis connection
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/evaluate")
async def evaluate(
    ref_file: str,
    hyp_file: str,
    algorithms: List[str] = ["dp", "epoch", "overlap", "taes", "ira"],
    use_cache: bool = True
):
    """Main evaluation endpoint with caching"""

    # Generate cache key
    cache_key = hashlib.md5(
        f"{ref_file}:{hyp_file}:{','.join(sorted(algorithms))}".encode()
    ).hexdigest()

    # Check cache
    if use_cache:
        cached = redis_client.get(cache_key)
        if cached:
            evaluation_counter.labels(
                algorithm="all",
                pipeline="cache",
                status="hit"
            ).inc()
            return json.loads(cached)

    # Run evaluation
    start = time.time()
    try:
        # Run both pipelines
        alpha_result = await run_alpha_pipeline(ref_file, hyp_file, algorithms)
        beta_result = await run_beta_pipeline(ref_file, hyp_file, algorithms)

        # Validate parity
        parity_report = validate_parity(alpha_result, beta_result)

        result = {
            "alpha": alpha_result,
            "beta": beta_result,
            "parity": parity_report,
            "duration": time.time() - start
        }

        # Cache result (expire in 1 hour)
        redis_client.setex(cache_key, 3600, json.dumps(result))

        evaluation_counter.labels(
            algorithm="all",
            pipeline="both",
            status="success"
        ).inc()

        evaluation_duration.labels(
            algorithm="all",
            pipeline="both"
        ).observe(time.time() - start)

        return result

    except Exception as e:
        evaluation_counter.labels(
            algorithm="all",
            pipeline="both",
            status="error"
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))
```

### Afternoon: Parallel Batch Processing

```python
# nedc_bench/api/batch.py
import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import multiprocessing as mp

class BatchProcessor:
    """Process multiple file pairs in parallel"""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(mp.cpu_count(), 4)
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)

    async def process_batch(
        self,
        file_pairs: List[tuple[str, str]],
        algorithms: List[str]
    ):
        """Process multiple evaluations in parallel"""

        # Create tasks
        loop = asyncio.get_event_loop()
        tasks = []

        for ref, hyp in file_pairs:
            task = loop.run_in_executor(
                self.executor,
                self._evaluate_single,
                ref, hyp, algorithms
            )
            tasks.append(task)

        # Wait for all with progress
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            print(f"Completed {i+1}/{len(tasks)}")

        return results

    def _evaluate_single(self, ref: str, hyp: str, algorithms: List[str]):
        """Run single evaluation in subprocess"""
        from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator

        orchestrator = DualPipelineOrchestrator()
        return orchestrator.evaluate_all(ref, hyp, algorithms)

@app.post("/batch")
async def batch_evaluate(
    file_pairs: List[dict],  # [{"ref": "path1", "hyp": "path2"}, ...]
    algorithms: List[str] = ["dp"],
    background_tasks: BackgroundTasks = None
):
    """Batch evaluation endpoint"""

    # Validate inputs
    pairs = [(p["ref"], p["hyp"]) for p in file_pairs]

    # Process in background if requested
    if background_tasks:
        job_id = str(uuid.uuid4())
        background_tasks.add_task(process_and_store, job_id, pairs, algorithms)
        return {"job_id": job_id, "status": "processing"}

    # Process immediately
    processor = BatchProcessor()
    results = await processor.process_batch(pairs, algorithms)
    return {"results": results}
```

---

## Day 3: Monitoring & Deployment

### Morning: Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nedc-bench-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

# Basic alerts
rule_files:
  - '/etc/prometheus/alerts.yml'
```

```yaml
# monitoring/alerts.yml
groups:
  - name: nedc_bench
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(nedc_evaluations_total{status="error"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowEvaluations
        expr: histogram_quantile(0.95, nedc_evaluation_duration_seconds) > 10
        for: 5m
        annotations:
          summary: "P95 latency > 10 seconds"

      - alert: ParityFailures
        expr: rate(nedc_parity_failures_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Parity validation failures detected"
```

### Afternoon: Simple Kubernetes Deployment (Optional but Educational)

```yaml
# k8s/deployment.yaml
# Simple single-file Kubernetes deployment
apiVersion: v1
kind: Namespace
metadata:
  name: nedc-bench
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nedc-bench
  namespace: nedc-bench
spec:
  replicas: 1  # Start simple
  selector:
    matchLabels:
      app: nedc-bench
  template:
    metadata:
      labels:
        app: nedc-bench
    spec:
      containers:
      - name: api
        image: nedc-bench/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: nedc-bench
  namespace: nedc-bench
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: nedc-bench
```

### Production Deployment Guide

```bash
# 1. Build and run with Docker Compose (RECOMMENDED)
docker-compose build
docker-compose up -d
docker-compose ps

# 2. Test the deployment
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# 3. Run a test evaluation
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "ref_file": "/data/ref/test.csv_bi",
    "hyp_file": "/data/hyp/test.csv_bi",
    "algorithms": ["dp", "epoch"]
  }'

# 4. View metrics
open http://localhost:9090  # Prometheus

# 5. (Optional) Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
kubectl get pods -n nedc-bench
kubectl port-forward -n nedc-bench svc/nedc-bench 8000:80
```

---

## What We're Shipping

### Essential Deliverables:
1. ✅ **Dockerized services** - Both pipelines containerized
2. ✅ **Docker Compose** - One command deployment
3. ✅ **FastAPI with caching** - Production API with Redis
4. ✅ **Parallel processing** - Batch evaluation support
5. ✅ **Prometheus metrics** - Basic monitoring
6. ✅ **Health checks** - Service availability
7. ✅ **Production docs** - How to deploy and operate

### Nice-to-Have (If Time):
8. ⭐ **Basic K8s manifest** - Learn Kubernetes basics
9. ⭐ **Simple CI/CD** - GitHub Actions for Docker builds

### Explicitly NOT Doing:
- ❌ Helm charts (overkill)
- ❌ Service mesh (unnecessary complexity)
- ❌ Multiple replicas (start simple)
- ❌ Grafana dashboards (Prometheus is enough)
- ❌ Distributed tracing (not needed for batch processing)

---

## Success Metrics (Realistic)

- ✅ **Deployment**: `docker-compose up` just works
- ✅ **Performance**: < 5 seconds for single evaluation
- ✅ **Reliability**: Health checks passing
- ✅ **Monitoring**: Can see metrics in Prometheus
- ✅ **Documentation**: Someone else can deploy it

---

## Learning Outcomes

1. **Docker best practices** - Multi-stage builds, health checks
2. **API design** - FastAPI, caching, async
3. **Monitoring** - Prometheus metrics
4. **Container orchestration** - Docker Compose (and basic K8s)
5. **Production readiness** - What actually matters for shipping

This is tight, focused, and actually shippable!