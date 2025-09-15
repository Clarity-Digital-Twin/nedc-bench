#!/usr/bin/env sh
set -e

# Respect environment variables for logging and worker count
LOG_LEVEL_RAW=${LOG_LEVEL:-info}
# Normalize to lowercase for uvicorn
LOG_LEVEL=$(echo "$LOG_LEVEL_RAW" | tr '[:upper:]' '[:lower:]')
MAX_WORKERS=${MAX_WORKERS:-1}

# Prepare Prometheus multiprocess directory if enabled
if [ -n "$PROMETHEUS_MULTIPROC_DIR" ]; then
  mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
  # Clean up old metric files to avoid stale counters on restart
  find "$PROMETHEUS_MULTIPROC_DIR" -type f -name '*.db' -delete 2>/dev/null || true
fi

exec uvicorn nedc_bench.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "$MAX_WORKERS" \
  --log-level "$LOG_LEVEL"
