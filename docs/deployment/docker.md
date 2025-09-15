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

## Run with Docker Compose
```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
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
- If readiness is 503, verify Redis connectivity or use `/api/v1/health`.
- Check logs: `docker logs <container>`.

## Related
- [Kubernetes Deployment](kubernetes.md)
- [Configuration Guide](configuration.md)
- [Overview](overview.md)
