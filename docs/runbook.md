# Production Runbook

This runbook covers day‑2 operations for the NEDC Bench API in Docker Compose and Kubernetes.

## Docker Compose (staging/dev)

- Start stack: `docker-compose up -d`
- Check health: `curl http://localhost:8000/api/v1/health`
- Readiness: `curl http://localhost:8000/api/v1/ready`
- Metrics: `curl http://localhost:8000/metrics`
- Logs: `docker-compose logs -f api`
- Stop: `docker-compose down`

## Kubernetes (production)

- Deploy: `kubectl apply -f k8s/`
- Check pods: `kubectl get pods`
- Check probes:
  - `kubectl describe pod <name>` (liveness/readiness events)
- Port‑forward for local test: `kubectl port-forward svc/nedc-bench-api 8000:80`
- Scale: `kubectl scale deploy/nedc-bench-api --replicas=4`
- Rollout status: `kubectl rollout status deploy/nedc-bench-api`
- Roll back: `kubectl rollout undo deploy/nedc-bench-api`

## Monitoring

- Prometheus: http://localhost:9090
- Key metrics to watch:
  - `nedc_evaluations_total` (rate, status)
  - `nedc_evaluation_duration_seconds` (latency)
  - `nedc_parity_failures_total` (should be ~0)
  - `nedc_active_evaluations` (current load)

## Troubleshooting

- High latency:
  - Check `nedc_active_evaluations` and API CPU/memory
  - Verify Redis reachable from API
  - Confirm cache hit rate (instrument if needed)
- Parity failures:
  - Review recent changes
  - Re‑run parity test suite
- Readiness failures:
  - Inspect Redis connection
  - Check background worker status (if applicable)

## Graceful Shutdown

- Compose: `docker-compose down` terminates containers; API should finish in‑flight requests before exit.
- Kubernetes: probes and termination grace allow requests to drain during rollout.

