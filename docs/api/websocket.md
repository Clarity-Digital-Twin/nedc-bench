# WebSocket API

Realtime progress and results are streamed over a WebSocket per job id.

## URL

- `ws://<host>:8000/ws/{job_id}`

## Connection

- Server accepts the connection immediately.
- If the job exists, the server sends an initial snapshot before registering for live updates.
- Heartbeats: the server emits `{ "type": "heartbeat" }` on ~30s idle; clients may send `"ping"` to receive `"pong"`.

## Event Types

- `initial`:
  - Shape: `{ "type": "initial", "job": { "id": string, "status": string, "created_at": ISO8601 } }`
- `status`:
  - Emitted on lifecycle changes: queued, processing, completed, failed
  - Shapes:
    - `{ "type": "status", "status": "queued", "message": string, "job_id": string, "created_at": ISO8601 }`
    - `{ "type": "status", "status": "processing", "message": string }`
    - `{ "type": "status", "status": "completed", "message": string }`
    - `{ "type": "status", "status": "failed", "error": string }`
- `algorithm`:
  - Per-algorithm progress and result payloads
  - Shapes:
    - `{ "type": "algorithm", "algorithm": "dp|epoch|overlap|ira|taes", "status": "running" }`
    - `{ "type": "algorithm", "algorithm": "...", "status": "completed", "result": { ... } }`
- `heartbeat`:
  - Shape: `{ "type": "heartbeat" }`
- `error`:
  - Shape: `{ "type": "error", "message": string }`

## Examples

### Python (websockets)

```python
import asyncio, json, websockets


async def tail(job_id: str):
    uri = f"ws://localhost:8000/ws/{job_id}"
    async with websockets.connect(uri) as ws:
        async for raw in ws:
            evt = json.loads(raw) if raw.startswith("{") else raw
            print(evt)


asyncio.run(tail("<JOB_ID>"))
```

### Node.js (ws)

```js
import WebSocket from 'ws';

const ws = new WebSocket('ws://localhost:8000/ws/<JOB_ID>');
ws.on('message', (data) => {
  console.log(data.toString());
});
```
