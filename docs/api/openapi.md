# OpenAPI Specification

The API exposes a live OpenAPI 3 schema and interactive documentation.

## Where to find it
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Raw schema: `http://localhost:8000/openapi.json`

## Programmatic access
```bash
curl http://localhost:8000/openapi.json > openapi.json
```

## Customization
- The app overrides `app.openapi` via `nedc_bench/api/docs.py` to set title, description, and tags.
- Tags:
  - `health`: health/readiness endpoints
  - `evaluation`: evaluation submission and retrieval
  - `websocket`: realtime updates (ws paths are not part of the OpenAPI schema)

## Notes
- WebSocket routes (`/ws/{job_id}`) are not included in OpenAPI by design.
- The Prometheus `/metrics` endpoint returns text; it is not documented in the schema.
