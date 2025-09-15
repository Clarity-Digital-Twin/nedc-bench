# Configuration Guide

> TODO: Extract from codebase, docker-compose.yml, and config files

## Environment Variables

### Core Settings
<!-- TODO: Extract from code -->
- `NEDC_NFC` - NEDC root directory
- `PYTHONPATH` - Python path configuration

### API Configuration
<!-- TODO: Extract from nedc_bench/api/ -->
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `WORKERS` - Number of workers

### Redis Configuration
<!-- TODO: Extract from docker-compose.yml -->
- `REDIS_URL` - Redis connection URL
- `REDIS_CACHE_TTL` - Cache TTL in seconds

### Database Configuration
<!-- TODO: If applicable -->

### Monitoring
<!-- TODO: Prometheus/metrics config -->
- `METRICS_ENABLED` - Enable metrics
- `METRICS_PORT` - Metrics port

## Configuration Files

### pyproject.toml
<!-- TODO: Extract key settings -->

### .env File
<!-- TODO: Environment file format -->
```env
# Example .env
```

## Pipeline Configuration

### Alpha Pipeline
<!-- TODO: Original NEDC configuration -->

### Beta Pipeline
<!-- TODO: Modern pipeline configuration -->

## Algorithm Parameters
<!-- TODO: Extract from algorithms -->

## Security Configuration
<!-- TODO: API keys, authentication -->

## Logging Configuration
<!-- TODO: Log levels, outputs -->

## Performance Tuning
<!-- TODO: Cache, workers, threads -->

## Related
- [Docker Deployment](docker.md)
- [Environment Variables Reference](../reference/configuration.md)
- [Troubleshooting](troubleshooting.md)