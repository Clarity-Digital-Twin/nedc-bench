# Python Client SDK

The API is simple to consume with `requests` and `websockets`. Below is a minimal helper that wraps common calls.

## Install dependencies

- `pip install requests websockets`

## Minimal client

```python
import json
import requests
import websockets
import asyncio


class NedcBenchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base = base_url.rstrip("/")

    def health(self) -> dict:
        return requests.get(f"{self.base}/api/v1/health").json()

    def submit(
        self,
        ref_path: str,
        hyp_path: str,
        algorithms: list[str] | None = None,
        pipeline: str = "dual",
    ) -> str:
        files = {
            "reference": open(ref_path, "rb"),
            "hypothesis": open(hyp_path, "rb"),
        }
        # Encode repeatable form fields as list of tuples for FastAPI
        data = [("pipeline", pipeline)]
        for alg in algorithms or ["all"]:
            data.append(("algorithms", alg))
        r = requests.post(f"{self.base}/api/v1/evaluate", files=files, data=data)
        r.raise_for_status()
        return r.json()["job_id"]

    def result(self, job_id: str) -> dict:
        r = requests.get(f"{self.base}/api/v1/evaluate/{job_id}")
        r.raise_for_status()
        return r.json()

    async def stream(self, job_id: str):
        async with websockets.connect(
            f"{self.base.replace('http', 'ws')}/ws/{job_id}"
        ) as ws:
            async for msg in ws:
                yield json.loads(msg)
```

## Usage

```python
c = NedcBenchClient()
job = c.submit(
    "data/ref/example.csv_bi", "data/hyp/example.csv_bi", algorithms=["dp", "taes"]
)
print("job:", job)

# Poll result
print(c.result(job)["status"])


# Or stream progress
async def run():
    async for evt in c.stream(job):
        print(evt)


asyncio.run(run())
```

## Notes

- `algorithms` can be any of: `dp`, `epoch`, `overlap`, `ira`, `taes`, or `all`.
- `pipeline` can be `alpha`, `beta`, or `dual`.
- See docs/api/websocket.md for event payloads.
