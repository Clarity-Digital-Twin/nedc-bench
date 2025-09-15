# API Examples

Practical examples for common API tasks.

## cURL

- Health check:
  - `curl http://localhost:8000/api/v1/health`

- Submit evaluation (multipart form):
  - `curl -X POST http://localhost:8000/api/v1/evaluate \
       -F "reference=@data/ref/example.csv_bi" \
       -F "hypothesis=@data/hyp/example.csv_bi" \
       -F "algorithms=dp" -F "algorithms=taes" \
       -F "pipeline=dual"`

- Get job result:
  - `curl http://localhost:8000/api/v1/evaluate/<JOB_ID>`

- List jobs (pagination):
  - `curl "http://localhost:8000/api/v1/evaluate?limit=20&offset=0&status=completed"`

## Python

```python
import requests

base = "http://localhost:8000"

files = {
    'reference': open('data/ref/example.csv_bi', 'rb'),
    'hypothesis': open('data/hyp/example.csv_bi', 'rb'),
}
data = [
    ('algorithms', 'dp'),
    ('algorithms', 'epoch'),  # repeatable field
    ('pipeline', 'dual'),
]

r = requests.post(f"{base}/api/v1/evaluate", files=files, data=data)
job_id = r.json()['job_id']

result = requests.get(f"{base}/api/v1/evaluate/{job_id}").json()
print(result['status'])
```

### Python async WebSocket tail
```python
import asyncio, json, websockets

async def follow(job_id: str):
    async with websockets.connect(f"ws://localhost:8000/ws/{job_id}") as ws:
        async for msg in ws:
            print(json.loads(msg))

asyncio.run(follow("<JOB_ID>"))
```

## JavaScript (Node)

```js
import fetch from 'node-fetch';
import FormData from 'form-data';
import fs from 'fs';

const form = new FormData();
form.append('reference', fs.createReadStream('data/ref/example.csv_bi'));
form.append('hypothesis', fs.createReadStream('data/hyp/example.csv_bi'));
form.append('algorithms', 'taes');
form.append('algorithms', 'dp');
form.append('pipeline', 'dual');

const res = await fetch('http://localhost:8000/api/v1/evaluate', { method: 'POST', body: form });
const { job_id } = await res.json();
console.log(job_id);
```
