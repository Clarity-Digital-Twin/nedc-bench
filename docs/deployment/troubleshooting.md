# Deployment Troubleshooting Guide

## Common Issues

### Docker

#### Container won’t start
```bash
docker logs <container>
docker inspect <container>
```
Check that the image was built, required env vars are set, and port 8000 is free.

#### Permission errors
Run containers without mounting unwritable directories, or adjust volume permissions.

#### Network issues
Verify `-p 8000:8000` mapping and that no firewall is blocking localhost.

### Kubernetes

#### CrashLoopBackOff
Inspect logs for missing env vars or startup exceptions. Ensure Redis is reachable if readiness is enabled.

#### ImagePullBackOff
Check registry credentials and image tag names.

#### OOMKilled / throttling
Increase memory/CPU limits; reduce workers; verify workload.

### API

#### 503 on `/api/v1/ready`
Background worker not running or Redis unreachable. Use `/api/v1/health` for a simple check.

#### 500 Internal Server Error
Validate input CSV_BI files; confirm algorithms/pipeline parameters; check server logs for stack traces.

#### Timeouts
Increase client timeout; check CPU contention and worker count; ensure Redis connectivity for caching.

## Debugging Tools

### Logs
```bash
# Docker logs
docker logs -f <container>

# Kubernetes logs
kubectl logs -f <pod>
```

### Shell Access
```bash
# Docker
docker exec -it <container> bash

# Kubernetes
kubectl exec -it <pod> -- bash
```

### Health Checks
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

## Known Pitfalls

### NEDC path resolution
Set `NEDC_NFC` and `PYTHONPATH` when running scripts manually. The API sets these automatically on startup.

### Parity mismatches
Use `uv run python scripts/compare_parity.py` to validate Beta vs Alpha.

## FAQ

### Q: Container exits immediately
A: Check entrypoint/command; ensure uvicorn is launched and no port conflict.

### Q: Can’t connect to Redis
A: Verify `REDIS_URL`, DNS, and service reachability. Fall back to health endpoint if readiness depends on Redis.

### Q: API returns unexpected metrics
A: Confirm algorithm selection and that inputs are proper CSV_BI files with matching durations.

## Related
- [Docker Deployment](docker.md)
- [Kubernetes Deployment](kubernetes.md)
- [Configuration](configuration.md)
- [Monitoring](monitoring.md)
