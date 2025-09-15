# Quickstart Guide

## 5-Minute Setup

### Prerequisites
- Python 3.10+
- UV (recommended) or pip

### Install
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e .[dev]
```

## First Evaluation

### Option A: Use the API
```bash
uv run uvicorn nedc_bench.api.main:app --reload
# Submit via curl (note: enum values are lowercase)
curl -s -X POST "http://localhost:8000/api/v1/evaluate" \
  -F reference=@data/csv_bi_parity/csv_bi_export_clean/ref/aaaaaajy_s001_t000.csv_bi \
  -F hypothesis=@data/csv_bi_parity/csv_bi_export_clean/hyp/aaaaaajy_s001_t000.csv_bi \
  -F algorithms=all -F pipeline=dual | jq

# Watch progress
wscat -c ws://localhost:8000/ws/<job_id>
```

### Option B: Use scripts (no CLI)
```bash
# Run all Beta algorithms and save SSOT
uv run python scripts/run_beta_batch.py

# Compare Alpha vs Beta parity
uv run python scripts/compare_parity.py
```

### Option C: Docker Compose
```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

## Understanding Output
- TP/FP/FN and FA/24h are returned per algorithm. See `docs/algorithms/metrics.md` for definitions.
- Epoch and IRA operate on fixed windows; TAES returns fractional counts; DP/Overlap return integer counts.

## Example Dataset
- Sample CSV_BI files live under `data/csv_bi_parity/csv_bi_export_clean/` with `ref/` and `hyp/` subfolders and list files in `lists/`.

## What’s Next
- [User Guide](user-guide/overview.md)
- [Algorithm Details](algorithms/overview.md)
- [API Docs](api/endpoints.md)
- [Deployment](deployment/overview.md)
