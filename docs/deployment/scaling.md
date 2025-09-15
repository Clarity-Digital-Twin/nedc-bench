# Scaling Guide

## Horizontal Scaling

### Add workers
```bash
uv run uvicorn nedc_bench.api.main:app --workers 4
```

### Load balancing
- Behind Nginx/Envoy/ALB, route to multiple API pods/containers.

## Vertical Scaling

### Resource Guidelines
| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| API       | 2 cores | 4 GB | Per worker |
| Redis     | 1 core | 2 GB | Cache size dependent |

### Performance Tuning
- Cache results via Redis to reduce recomputation.
- Ensure inputs are prevalidated to avoid retries.

## Auto-scaling
- Kubernetes HPA based on CPU or custom latency metrics.

## Performance Testing
- Use k6/Locust for HTTP load; verify latency targets and error rates.

## Metrics to Watch
- p95/p99 latency, error rate, CPU/memory, cache hit rate.

## Related
- [Monitoring](monitoring.md)
- [Configuration](configuration.md)
- [Kubernetes Deployment](kubernetes.md)
