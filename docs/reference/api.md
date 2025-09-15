# API Reference

For the complete, up-to-date details see:
- Endpoints: `docs/api/endpoints.md`
- WebSocket: `docs/api/websocket.md`
- OpenAPI: `docs/api/openapi.md`
- Python client: `docs/api/python-client.md`
- Examples: `docs/api/examples.md`

## Key Endpoints
- `POST /api/v1/evaluate` — submit a job. Multipart form with:
  - `reference` (file), `hypothesis` (file)
  - `algorithms` (repeatable form field), `pipeline` (dual|alpha|beta)
- `GET /api/v1/evaluate/{job_id}` — fetch results for a job
- `GET /api/v1/evaluate?limit=&offset=&status=` — list jobs
- `GET /api/v1/health` — liveness
- `GET /api/v1/ready` — readiness (checks worker and Redis)
- `GET /metrics` — Prometheus metrics
- `WS /ws/{job_id}` — realtime progress, heartbeats, ping/pong

Models and response shapes are defined in `nedc_bench/api/models/` and shown in the OpenAPI UI at `/docs`.
