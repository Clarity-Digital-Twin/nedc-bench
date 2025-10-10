# Docker Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2

## Build the API image

```bash
docker build -f Dockerfile.api -t nedc-bench/api:latest .
```

## Run with Docker

```bash
docker run --rm -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  nedc-bench/api:latest

curl http://localhost:8000/api/v1/health
```

Notes:

- The image defaults to a single uvicorn worker (`--workers 1`) to keep metrics simple. For higher concurrency, override the command:
  ```bash
  docker run --rm -p 8000:8000 \
    nedc-bench/api:latest \
    uvicorn nedc_bench.api.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- On Linux, if `host.docker.internal` is unavailable, connect Redis via bridge network or use the Compose stack.

Multi-worker metrics:

- When running with multiple workers, enable Prometheus multiprocess mode:
  ```bash
  docker run --rm -p 8000:8000 \
    -e PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc \
    -e MAX_WORKERS=4 \
    nedc-bench/api:latest
  ```
  The entrypoint will clean the directory on start; `/metrics` will aggregate across workers.

## Run with Docker Compose

```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

Override workers in Compose by adding a custom `command:` to the `api` service if needed:

```yaml
services:
  api:
    command: [
      "uvicorn", "nedc_bench.api.main:app",
      "--host", "0.0.0.0", "--port", "8000",
      "--workers", "4"
    ]
```

## Environment Variables

- `NEDC_NFC` defaults to `/app/nedc_eeg_eval/v6.0.0` inside the image.
- `REDIS_URL` defaults to `redis://redis:6379` in Compose.
- `CACHE_TTL_SECONDS` controls cache TTL (default 86400).

## Networking

- API listens on port `8000`.
- WebSocket endpoint is `/ws/{job_id}`.

## Health Checks

- Liveness: `GET /api/v1/health` (200 OK when process is up).
- Readiness: `GET /api/v1/ready` (requires worker running and Redis reachable).

## Troubleshooting

### Common Issues and Solutions

#### Docker Compose v1 vs v2 (Windows/WSL)
```bash
# If you see "docker-compose: command not found" or version errors:
# Use the v2 syntax (space instead of hyphen):
docker compose up -d  # ✅ Correct (v2)
docker-compose up -d  # ❌ Old syntax (v1)
```

#### Line Ending Issues (Windows/WSL)
```bash
# Fix CRLF line endings in entrypoint script
sed -i 's/\r$//' docker-entrypoint.sh
```

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Stop conflicting containers
docker ps
docker stop <container_id>
```

#### Container Keeps Restarting
```bash
# Check logs for errors
docker logs nedc-bench-api-1 --tail 50

# Common fix: rebuild with clean cache
docker compose down
docker compose build --no-cache
docker compose up -d
```

#### API Returns 503 or Connection Refused
- Verify Redis is running: `docker ps | grep redis`
- Check API health: `curl http://localhost:8000/api/v1/health`
- Review logs: `docker compose logs api --tail 100`

### Troubleshooting Checklist

1. ✅ Docker version >= 20.10: `docker --version`
2. ✅ Docker Compose v2 installed: `docker compose version`
3. ✅ Sufficient disk space: `df -h` (Linux/Mac) or check drive properties (Windows)
4. ✅ Ports available: Check 8000, 9090, 3000 not in use
5. ✅ Containers running: `docker ps`
6. ✅ API healthy: `curl http://localhost:8000/api/v1/health`

## Related

- [Kubernetes Deployment](kubernetes.md)
- [Configuration Guide](configuration.md)
- [Overview](overview.md)
