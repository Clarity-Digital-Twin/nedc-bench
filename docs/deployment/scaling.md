# Scaling Guide

> TODO: Extract from performance testing and deployment experience

## Horizontal Scaling

### Adding Workers
<!-- TODO: Worker configuration -->
```bash
# Scale workers
uvicorn --workers 4
```

### Load Balancing
<!-- TODO: Load balancer configuration -->

### Session Affinity
<!-- TODO: If needed -->

## Vertical Scaling

### Resource Requirements
<!-- TODO: CPU/Memory requirements -->

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| API | 2 cores | 4GB | Per worker |
| Redis | 1 core | 2GB | Cache size dependent |

### Performance Tuning
<!-- TODO: Optimization settings -->

## Caching Strategy

### Redis Scaling
<!-- TODO: Redis cluster/sentinel -->

### Cache Warm-up
<!-- TODO: Pre-loading cache -->

## Database Scaling
<!-- TODO: If applicable -->

## Queue Scaling
<!-- TODO: If using task queues -->

## Auto-scaling

### Kubernetes HPA
<!-- TODO: HPA configuration -->
```yaml
# HPA example
```

### AWS Auto-scaling
<!-- TODO: If applicable -->

## Performance Testing

### Load Testing
<!-- TODO: How to load test -->
```bash
# Example with locust/k6
```

### Benchmarks
<!-- TODO: Performance benchmarks -->

## Monitoring Scale

### Metrics to Watch
<!-- TODO: Key scaling metrics -->
- Request latency p95/p99
- CPU utilization
- Memory usage
- Cache hit rate

## Cost Optimization
<!-- TODO: Cost-effective scaling -->

## Related
- [Monitoring](monitoring.md)
- [Configuration](configuration.md)
- [Kubernetes Deployment](kubernetes.md)