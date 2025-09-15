# Monitoring Guide

> TODO: Extract from nedc_bench/monitoring/ if exists

## Metrics

### Prometheus Metrics
<!-- TODO: Available metrics -->
- Request latency
- Request count
- Error rate
- Algorithm execution time

### Metrics Endpoint
<!-- TODO: /metrics endpoint -->
```bash
curl http://localhost:8000/metrics
```

## Logging

### Log Configuration
<!-- TODO: Extract from logging setup -->

### Log Levels
<!-- TODO: Available log levels -->

### Structured Logging
<!-- TODO: JSON logging format -->

## Health Checks

### Liveness Probe
<!-- TODO: /health/live endpoint -->

### Readiness Probe
<!-- TODO: /health/ready endpoint -->

## Dashboards

### Grafana
<!-- TODO: Dashboard configuration -->

### Example Queries
<!-- TODO: Useful Prometheus queries -->

## Alerts

### Alert Rules
<!-- TODO: Prometheus alert rules -->

### Notification Channels
<!-- TODO: Alertmanager configuration -->

## Performance Monitoring

### APM Integration
<!-- TODO: If applicable -->

### Tracing
<!-- TODO: Distributed tracing -->

## Troubleshooting

### Common Issues
<!-- TODO: Monitoring troubleshooting -->

### Debug Endpoints
<!-- TODO: Debug/profiling endpoints -->

## Related
- [Configuration](configuration.md)
- [Scaling](scaling.md)
- [Troubleshooting](troubleshooting.md)