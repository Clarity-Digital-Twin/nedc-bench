# Debugging Guide

## Common Issues
- NEDC path not set: ensure `NEDC_NFC` points to the v6.0.0 root. The API sets a default to `nedc_eeg_eval/v6.0.0` during startup and adjusts `PYTHONPATH` to its `lib/`.
- WebSocket appears silent: connect to `ws://localhost:8000/ws/{job_id}` after submitting; expect an `initial` event followed by progress, with periodic `heartbeat`.
- Readiness probe fails: `/api/v1/ready` returns 503 if the background worker is not running or Redis is unreachable.
- Run script path: `./run_nedc.sh` expects lists under `nedc_eeg_eval/v6.0.0/data/lists/`.

## Debugging Tools
- Enable verbose traces in tests: `pytest -vv -s`.
- Inspect last WS event for a job: use `nedc_bench/api/services/websocket_manager.py` behavior (last event replay on connect).
- Compare Alpha vs Beta outputs: `python scripts/compare_parity.py --verbose`.

## Logging
- API logs: configured in `nedc_bench/api/main.py` (basicConfig INFO). Run with higher verbosity using uvicorn, e.g.:
  - `uv run uvicorn nedc_bench.api.main:app --reload --log-level debug`.
- Worker lifecycle and job state transitions are logged by `job_manager` and `processor`.
