from __future__ import annotations

import asyncio
from typing import Any

import pytest

# Skip API tests if FastAPI isn't available
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # type: ignore

from nedc_bench.api.main import app  # type: ignore
from nedc_bench.api.middleware.rate_limit import rate_limiter


@pytest.fixture(scope="module")
def client() -> Any:
    with TestClient(app) as c:
        yield c


def test_health_endpoint_ok(client: Any) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_metrics_endpoint_exposes_text(client: Any) -> None:
    res = client.get("/metrics")
    assert res.status_code == 200
    # Either real prometheus content-type or fallback text/plain
    assert res.headers["content-type"].startswith("text/plain")
    # Body may be empty if prometheus_client is absent; that's fine


@pytest.mark.integration
def test_readiness_ok_when_worker_and_redis_ok(client: Any, monkeypatch: Any) -> None:
    # Worker is started by app lifespan in TestClient context; patch Redis ping only
    async def ping_ok() -> bool:  # noqa: D401
        return True

    # Patch the redis_cache.ping function in the readiness endpoint module
    monkeypatch.setattr("nedc_bench.api.endpoints.health.redis_cache.ping", ping_ok, raising=False)

    res = client.get("/api/v1/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}


@pytest.mark.integration
def test_readiness_fails_when_worker_down(client: Any, monkeypatch: Any) -> None:
    # Force job_manager.is_running() to return False
    monkeypatch.setattr("nedc_bench.api.endpoints.health.job_manager.is_running", lambda: False)
    res = client.get("/api/v1/ready")
    assert res.status_code == 503
    assert "Worker not running" in res.text


@pytest.mark.integration
def test_readiness_fails_when_redis_down(client: Any, monkeypatch: Any) -> None:
    # Ensure worker check passes, then fail Redis ping
    monkeypatch.setattr("nedc_bench.api.endpoints.health.job_manager.is_running", lambda: True)

    async def ping_fail() -> bool:
        return False

    monkeypatch.setattr(
        "nedc_bench.api.endpoints.health.redis_cache.ping", ping_fail, raising=False
    )

    res = client.get("/api/v1/ready")
    assert res.status_code == 503
    assert "Redis not reachable" in res.text


@pytest.mark.integration
def test_rate_limit_returns_429(client: Any, monkeypatch: Any) -> None:
    # Make limiter very small and reset its state
    rate_limiter.requests_per_minute = 3
    rate_limiter.requests = {}

    # Hit a cheap endpoint repeatedly from same client
    successes = 0
    status_429 = 0
    for _ in range(6):
        r = client.get("/api/v1/health")
        if r.status_code == 200:
            successes += 1
        if r.status_code == 429:
            status_429 += 1

    assert successes >= 1
    assert status_429 >= 1
    # Ensure Retry-After header present when limited
    if status_429:
        r = client.get("/api/v1/health")
        if r.status_code == 429:
            assert r.headers.get("Retry-After") == "60"
