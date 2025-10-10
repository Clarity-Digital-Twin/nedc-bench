# API Endpoints Reference

This reference reflects the current FastAPI app in `nedc_bench/api/`.

## Base URLs

- REST: `http://localhost:8000`
- OpenAPI UI: `http://localhost:8000/docs` (Swagger), `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Evaluation

- POST `/api/v1/evaluate`

  - Description: Submit a job to evaluate reference vs hypothesis using one or more algorithms.
  - Consumes: `multipart/form-data`
  - Form fields:
    - `reference` (file): Reference `.csv_bi` file
    - `hypothesis` (file): Hypothesis `.csv_bi` file
    - `algorithms` (repeatable string): `dp`, `epoch`, `overlap`, `ira`, `taes`, or `all` (send as repeated `algorithms` fields in form data)
    - `pipeline` (string): `alpha`, `beta`, or `dual` (default: `dual`)
  - Response: `EvaluationResponse`
    - `job_id` (string)
    - `status` (string) — `queued` on submit
    - `created_at` (ISO 8601)
    - `message` (string)

- GET `/api/v1/evaluate/{job_id}`

  - Description: Fetch the current status/result for a job.
  - Response: `EvaluationResult`
    - Always: `job_id`, `status` (`queued|processing|completed|failed`), `created_at`, `completed_at?`, `pipeline`, `error?`
    - If single algorithm requested: convenience fields `alpha_result?`, `beta_result?`, `parity_passed?`, `parity_report?`, `alpha_time?`, `beta_time?`, `speedup?`
    - If multiple algorithms: `results` is a map keyed by algorithm name

- GET `/api/v1/evaluate`

  - Description: List jobs with pagination and optional status filter.
  - Query params: `limit` (int, default 10), `offset` (int, default 0), `status` (string, optional)
  - Response: `EvaluationResult[]`

## Health

- GET `/api/v1/health`

  - Description: Liveness probe.
  - Response: `{ "status": "healthy" }`

- GET `/api/v1/ready`

  - Description: Readiness probe; verifies worker loop and Redis reachability.
  - 200 on success: `{ "status": "ready" }`
  - 503 if background worker not running or Redis not reachable.

## Metrics

- GET `/metrics`
  - Description: Prometheus metrics in text format.
  - Media type: `text/plain; version=0.0.4`
  - Note: If `prometheus_client` is not installed, returns an empty body with the same media type.

## WebSocket

- WS `ws://localhost:8000/ws/{job_id}`
  - Description: Real-time job progress and results.
  - Initial server message (if job exists):
    - `{ "type": "initial", "job": { "id": string, "status": string, "created_at": ISO8601 } }`
  - Heartbeat: server sends `{ "type": "heartbeat" }` every ~30s of inactivity; client may send `"ping"` to receive `"pong"`.
  - Progress events (broadcasts): see WebSocket page for full schema.
