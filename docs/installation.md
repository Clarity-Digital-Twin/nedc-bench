# Installation Guide

## System Requirements
- Python 3.10+ (3.10 and 3.11 tested in CI)
- OS: Linux, Windows (CI), macOS (developer-supported)
- Sufficient disk space for dependencies and sample data

## Install with UV (recommended)
UV is a fast Python package manager.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Linux/macOS shells will add $HOME/.cargo/bin to PATH; on Windows, use the PowerShell installer.

# Install project in editable mode with dev tools
uv pip install -e .[dev]

# Optional: install docs and API extras
uv pip install -e .[docs,api]
```

## Install with pip
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
```

## Run the API locally
```bash
uv run uvicorn nedc_bench.api.main:app --reload
# Open http://localhost:8000/docs
```

## Docker
```bash
# Build API image
docker build -f Dockerfile.api -t nedc-bench/api:latest .

# Run container
docker run --rm -p 8000:8000 nedc-bench/api:latest
```

## Docker Compose
```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

## Verify setup
- Lint and typecheck: `make lint && make typecheck`
- Run tests: `make test`
- Parity check (optional): `uv run python scripts/compare_parity.py`

## Troubleshooting
- Ensure Python 3.10+ is active: `python --version`
- If `/api/v1/ready` is 503 locally, Redis may be unavailable; use `/api/v1/health` for a simple health check.
- If Alpha pipeline fails, verify `NEDC_NFC` and `PYTHONPATH` are set or start via the API which sets them.

## Next Steps
- Read the [Quickstart](quickstart.md)
- Explore the [Algorithms](algorithms/overview.md)
- Use the [API](api/endpoints.md)
