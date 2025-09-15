# Migrating from NEDC v6.0.0

This guide highlights key differences and how to adopt NEDC‑BENCH while preserving results.

## Key Differences
- Dual pipeline: Original NEDC (Alpha) is vendored for reference; Beta reimplements algorithms with exact semantics.
- Packaging: Modern Python package (>=3.10) with `uv`, `ruff`, `mypy`, and FastAPI for a REST/WebSocket API.
- I/O: Inputs remain CSV_BI. Outputs are structured JSON from Beta; Alpha textual summaries are parsed for parity.
- Environment: API auto-sets `NEDC_NFC` and `PYTHONPATH` for Alpha; manual exports still work for scripts.

## Migration Steps
1. Keep your CSV_BI datasets unchanged.
2. Choose a runner:
   - API: `uv run uvicorn nedc_bench.api.main:app --reload`
   - Scripts: `python scripts/run_beta_batch.py` or `./run_nedc.sh` for Alpha
3. Validate parity using `python scripts/compare_parity.py`.
4. Integrate with your systems via the REST API (`/api/v1/evaluate`, `/ws/{job_id}`).

## Compatibility
- Algorithms: TAES, Epoch, Overlap, DP, IRA match NEDC v6.0.0 by construction.
- Python: Minimum 3.10. Alpha code runs via API with adjusted `PYTHONPATH`.
- Output: For automated pipelines, prefer Beta JSON outputs; they map 1:1 to NEDC metrics.
