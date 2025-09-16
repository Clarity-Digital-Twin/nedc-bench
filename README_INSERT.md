# Docker Deployment Guide

## Quick Start with Docker

The NEDC-BENCH platform is fully containerized and production-ready. This guide covers deployment and common issues.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2 (plugin version recommended)
- 4GB available RAM minimum
- Ports 8000, 9090, 3000 available

### Basic Deployment

```bash
# Clone repository
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench

# Start all services
docker compose up -d --build

# Verify health
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy"}
```

### Services Overview

| Service    | Port | Purpose                     | URL                        |
| ---------- | ---- | --------------------------- | -------------------------- |
| API        | 8000 | REST API for EEG evaluation | http://localhost:8000/docs |
| Redis      | 6379 | Job queue and caching       | Internal only              |
| Prometheus | 9090 | Metrics collection          | http://localhost:9090      |
| Grafana    | 3000 | Monitoring dashboards       | http://localhost:3000      |

### Testing with Sample Data

The repository includes CSV test data for validation:

```bash
# Single file evaluation
REF_FILE="data/csv_bi_parity/csv_bi_export_clean/ref/aaaaaajy_s001_t000.csv_bi"
HYP_FILE="data/csv_bi_parity/csv_bi_export_clean/hyp/aaaaaajy_s001_t000.csv_bi"

curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -F "reference=@$REF_FILE" \
  -F "hypothesis=@$HYP_FILE" \
  -F "algorithms=taes" \
  -F "algorithms=epoch" \
  -F "algorithms=ira" \
  -F "pipeline=beta"
```

### Common Issues and Solutions

#### Docker Compose Not Found

```bash
# Install Docker Compose v2 plugin (recommended)
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-linux-x86_64 \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
```

#### Line Ending Issues (Windows/WSL)

```bash
# Fix CRLF line endings in entrypoint script
sed -i 's/\r$//' docker-entrypoint.sh
```

#### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting containers
docker ps
docker stop <container_id>
```

#### Container Keeps Restarting

```bash
# Check logs
docker logs nedc-bench-api-1 --tail 50

# Common fix: rebuild with clean cache
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Production Configuration

For production deployments, configure environment variables:

```bash
# Create .env file
cat > .env << EOF
LOG_LEVEL=WARNING
MAX_WORKERS=8
REDIS_URL=redis://redis:6379
GRAFANA_PASSWORD=secure_password_here
EOF

# Deploy with production settings
docker compose --env-file .env up -d
```

### Monitoring and Logs

```bash
# View API logs
docker logs -f nedc-bench-api-1

# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Access Grafana dashboards
# Default credentials: admin/admin
open http://localhost:3000

# Query Prometheus metrics
curl http://localhost:9090/metrics
```

### Scaling for High Load

```yaml
# docker-compose.override.yml for scaling
services:
  api:
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Data Persistence

Redis data and Grafana configurations persist in Docker volumes:

```bash
# List volumes
docker volume ls | grep nedc-bench

# Backup Redis data
docker run --rm -v nedc-bench_redis_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data

# Clean up volumes (WARNING: deletes data)
docker compose down -v
```

### API Usage Examples

#### Submit Evaluation Job

```python
import requests

with open("ref.csv_bi", "rb") as ref, open("hyp.csv_bi", "rb") as hyp:
    response = requests.post(
        "http://localhost:8000/api/v1/evaluate",
        files={"reference": ref, "hypothesis": hyp},
        data={
            "algorithms": ["taes", "epoch", "ira"],
            "pipeline": "dual",  # Run both alpha and beta, verify parity
        },
    )
    job_id = response.json()["job_id"]
```

#### Check Job Status

```python
result = requests.get(f"http://localhost:8000/api/v1/evaluate/{job_id}")
print(result.json())
```

### Troubleshooting Checklist

1. ✅ Docker version >= 20.10: `docker --version`
1. ✅ Docker Compose v2 installed: `docker compose version`
1. ✅ Sufficient disk space: `df -h`
1. ✅ Ports available: `netstat -tulpn | grep -E '(8000|9090|3000)'`
1. ✅ Containers running: `docker ps`
1. ✅ API healthy: `curl http://localhost:8000/api/v1/health`

### Performance Benchmarks

On a standard deployment (4 CPU cores, 8GB RAM):

- Single evaluation: ~100ms for TAES scoring
- Throughput: ~50 evaluations/second
- Redis cache hit rate: >95% for repeated files
- API latency p95: \<200ms

### Integration with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Test NEDC-BENCH API
  run: |
    docker compose up -d --wait
    ./scripts/integration_test.sh
    docker compose down
```

### Security Notes

- API runs as non-root user (UID 10001)
- Redis is not exposed externally by default
- Enable TLS termination with reverse proxy for production
- Rotate Grafana admin password immediately

______________________________________________________________________

## Local Development (Without Docker)

If you prefer running without Docker:

```bash
# Create virtual environment
uv venv && source .venv/bin/activate

# Install with API dependencies
uv pip install -e ".[api]"

# Set environment variables
export NEDC_NFC=$PWD/nedc_eeg_eval/v6.0.0
export PYTHONPATH=$NEDC_NFC/lib:$PYTHONPATH

# Start API server
uvicorn nedc_bench.api.main:app --host 0.0.0.0 --port 8000

# Note: Redis required separately for job queuing
# Install: sudo apt-get install redis-server
# Start: redis-server
```

______________________________________________________________________

For more details, see the full documentation at `/docs` or the API documentation at http://localhost:8000/docs once deployed.
