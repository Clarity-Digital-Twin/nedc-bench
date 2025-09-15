# Kubernetes Deployment Guide

## Prerequisites
- A Kubernetes cluster and `kubectl` configured
- Optional: Redis, Prometheus, Grafana via official Helm charts

## Deploy
```bash
# Apply your manifests (example directory)
kubectl apply -f k8s/

# Check status
kubectl get deploy,svc,pod
kubectl rollout status deploy/nedc-bench-api

# Port-forward for local testing
kubectl port-forward svc/nedc-bench-api 8000:80
curl http://localhost:8000/api/v1/health
```

## Configuration
- Set `REDIS_URL` to your cluster DNS (e.g., `redis.default.svc.cluster.local:6379`).
- NEDC paths are set inside the image (defaults to `/app/nedc_eeg_eval/v6.0.0`).

## Scaling
- Increase replicas: `kubectl scale deploy/nedc-bench-api --replicas=4`.
- Add HPA for CPU or latency-based scaling.

## Monitoring
- Expose `/metrics` and scrape with Prometheus (ServiceMonitor recommended).

## Troubleshooting
- Inspect pod logs: `kubectl logs -f <pod>`.
- Readiness failing: verify Redis connectivity and worker status.

## Related
- [Docker Deployment](docker.md)
- [Configuration Guide](configuration.md)
- [Monitoring](monitoring.md)
