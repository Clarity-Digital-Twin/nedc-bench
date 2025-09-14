# Phase 5: Production - Performance, Monitoring, and Deployment
## Vertical Slice Goal: Production-Ready Platform with Full Observability

### Duration: 5 Days

### Success Criteria (TDD)
- [ ] Docker Compose deployment working
- [ ] Kubernetes manifests validated
- [ ] Monitoring & alerting configured
- [ ] Performance optimizations complete
- [ ] Production documentation ready

### Day 1: Production Docker Setup

#### Morning: Multi-stage Docker Builds
```python
# tests/test_docker_production.py
def test_docker_image_size():
    """Production images are optimized"""
    alpha_size = get_docker_image_size("nedc-bench/alpha:latest")
    beta_size = get_docker_image_size("nedc-bench/beta:latest")

    assert alpha_size < 500_000_000  # < 500MB
    assert beta_size < 200_000_000   # < 200MB (no legacy code)
```

#### Afternoon: Docker Compose Stack
```yaml
# docker-compose.yml
version: '3.8'

services:
  alpha:
    image: nedc-bench/alpha:${VERSION:-latest}
    restart: always
    environment:
      - NEDC_NFC=/opt/nedc
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./data:/data:ro
      - ./output:/output
    healthcheck:
      test: ["CMD", "python", "-c", "import nedc_eeg_eval"]
      interval: 30s
      timeout: 10s
      retries: 3

  beta:
    image: nedc-bench/beta:${VERSION:-latest}
    restart: always
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data:/data:ro
      - ./output:/output
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api:
    image: nedc-bench/api:${VERSION:-latest}
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ALPHA_URL=http://alpha:8001
      - BETA_URL=http://beta:8002
      - REDIS_URL=redis://redis:6379
    depends_on:
      - alpha
      - beta
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - ./monitoring/dashboards:/var/lib/grafana/dashboards
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Day 2: Performance Optimization

#### Morning: Caching Layer
```python
# tests/test_caching.py
@pytest.mark.integration
async def test_redis_caching():
    """Results are cached correctly"""
    cache = RedisCache()

    # First call - should compute
    start = time.time()
    result1 = await orchestrator.evaluate(ref, hyp, ["taes"])
    time1 = time.time() - start

    # Second call - should use cache
    start = time.time()
    result2 = await orchestrator.evaluate(ref, hyp, ["taes"])
    time2 = time.time() - start

    assert result1 == result2
    assert time2 < time1 * 0.1  # 10x faster from cache
```

#### Afternoon: Parallel Processing
```python
# performance/parallel.py
import asyncio
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

class ParallelEvaluator:
    """Parallel processing for multiple files"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)

    async def evaluate_batch(self,
                           file_pairs: List[Tuple[Path, Path]],
                           algorithm: str) -> List[Dict]:
        """Process multiple file pairs in parallel"""

        loop = asyncio.get_event_loop()

        # Create tasks for parallel execution
        tasks = []
        for ref, hyp in file_pairs:
            task = loop.run_in_executor(
                self.executor,
                self._evaluate_single,
                ref, hyp, algorithm
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        return results

    def _evaluate_single(self, ref: Path, hyp: Path, algorithm: str) -> Dict:
        """Single evaluation in separate process"""
        # This runs in a separate process
        evaluator = create_evaluator(algorithm)
        return evaluator.evaluate(ref, hyp)
```

### Day 3: Monitoring & Observability

#### Morning: Prometheus Metrics
```python
# tests/test_metrics.py
def test_prometheus_metrics():
    """Metrics are exposed correctly"""
    response = requests.get("http://localhost:8000/metrics")

    assert response.status_code == 200
    metrics = response.text

    # Check key metrics exist
    assert "nedc_evaluations_total" in metrics
    assert "nedc_evaluation_duration_seconds" in metrics
    assert "nedc_parity_failures_total" in metrics
    assert "nedc_pipeline_errors_total" in metrics
```

#### Afternoon: Instrumentation
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
evaluation_counter = Counter(
    'nedc_evaluations_total',
    'Total number of evaluations',
    ['algorithm', 'pipeline', 'status']
)

evaluation_duration = Histogram(
    'nedc_evaluation_duration_seconds',
    'Evaluation duration in seconds',
    ['algorithm', 'pipeline'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

parity_failures = Counter(
    'nedc_parity_failures_total',
    'Total parity validation failures',
    ['algorithm']
)

active_evaluations = Gauge(
    'nedc_active_evaluations',
    'Number of evaluations currently running'
)

def track_evaluation(algorithm: str, pipeline: str):
    """Decorator to track evaluation metrics"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            active_evaluations.inc()
            start = time.time()

            try:
                result = await func(*args, **kwargs)
                evaluation_counter.labels(
                    algorithm=algorithm,
                    pipeline=pipeline,
                    status='success'
                ).inc()
                return result

            except Exception as e:
                evaluation_counter.labels(
                    algorithm=algorithm,
                    pipeline=pipeline,
                    status='error'
                ).inc()
                raise

            finally:
                duration = time.time() - start
                evaluation_duration.labels(
                    algorithm=algorithm,
                    pipeline=pipeline
                ).observe(duration)
                active_evaluations.dec()

        return wrapper
    return decorator
```

### Day 4: Kubernetes Deployment

#### Morning: Kubernetes Manifests
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nedc-bench-api
  labels:
    app: nedc-bench
    component: api
spec:
  replicas: 3
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
        - name: ALPHA_URL
          value: "http://alpha-service:8001"
        - name: BETA_URL
          value: "http://beta-service:8002"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nedc-bench-api
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

#### Afternoon: Helm Chart
```yaml
# helm/nedc-bench/values.yaml
replicaCount:
  api: 3
  alpha: 2
  beta: 2

image:
  repository: nedc-bench
  pullPolicy: IfNotPresent
  tag: ""  # Override with --set image.tag=v1.0.0

service:
  type: LoadBalancer
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: api.nedc-bench.io
      paths:
        - path: /
          pathType: Prefix

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

monitoring:
  prometheus:
    enabled: true
    serviceMonitor:
      enabled: true
  grafana:
    enabled: true
    dashboards:
      enabled: true
```

### Day 5: Production Readiness

#### Morning: Health Checks & Readiness
```python
# tests/test_production_ready.py
class TestProductionReadiness:
    """Verify production readiness"""

    def test_health_endpoints(self):
        """All health endpoints work"""
        endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/ready",
            "http://localhost:8000/metrics"
        ]

        for endpoint in endpoints:
            response = requests.get(endpoint)
            assert response.status_code == 200

    def test_graceful_shutdown(self):
        """Service shuts down gracefully"""
        # Start service
        process = start_service()

        # Send SIGTERM
        process.terminate()

        # Should finish current requests
        time.sleep(5)

        # Should be stopped
        assert process.poll() is not None

    def test_rate_limiting(self):
        """Rate limiting works"""
        # Send many requests quickly
        responses = []
        for _ in range(150):
            r = requests.get("http://localhost:8000/evaluate")
            responses.append(r.status_code)

        # Some should be rate limited
        assert 429 in responses  # Too Many Requests
```

#### Afternoon: Documentation & Runbook
```markdown
# Production Runbook

## Deployment

### Docker Compose (Development/Staging)
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f api
```

### Kubernetes (Production)
```bash
helm install nedc-bench ./helm/nedc-bench \
  --set image.tag=v1.0.0 \
  --set ingress.hosts[0].host=api.nedc-bench.io
```

## Monitoring

### Key Metrics to Watch
- `nedc_evaluations_total` - Request rate
- `nedc_evaluation_duration_seconds` - Latency
- `nedc_parity_failures_total` - Parity issues
- `nedc_active_evaluations` - Current load

### Alerts
- Parity failure rate > 1%
- P95 latency > 5 seconds
- Error rate > 0.1%
- Memory usage > 80%

## Troubleshooting

### High Latency
1. Check `nedc_active_evaluations` - may be overloaded
2. Check cache hit rate
3. Review slow query logs

### Parity Failures
1. Check recent deployments
2. Review algorithm changes
3. Compare Alpha and Beta logs
4. Run validation test suite

### Scaling
- Horizontal: Add more replicas
- Vertical: Increase resource limits
```

### Deliverables Checklist
- [ ] `docker-compose.yml` - Production stack
- [ ] `Dockerfile.prod` - Optimized images
- [ ] `k8s/` - Kubernetes manifests
- [ ] `helm/nedc-bench/` - Helm chart
- [ ] `monitoring/` - Prometheus & Grafana configs
- [ ] `performance/` - Optimization code
- [ ] `docs/runbook.md` - Operations guide
- [ ] `docs/deployment.md` - Deployment guide

### Definition of Done
1. ✅ Production Docker stack working
2. ✅ Kubernetes deployment validated
3. ✅ Monitoring & alerting configured
4. ✅ Performance targets met
5. ✅ Documentation complete

### Platform Success Metrics
- 🎯 < 100ms latency (P50)
- 🎯 < 1 second latency (P95)
- 🎯 > 99.9% uptime
- 🎯 100% parity between pipelines
- 🎯 > 100 requests/second capacity

---
## Notes
- Use multi-stage Docker builds for size
- Implement circuit breakers for resilience
- Add distributed tracing for debugging
- Consider CDN for static assets
- Plan for database backups