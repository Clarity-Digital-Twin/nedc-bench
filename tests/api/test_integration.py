import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nedc_bench.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sample_files():
    ref_file = Path("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi")
    hyp_file = Path("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi")
    assert ref_file.exists() and hyp_file.exists()
    return {
        "reference": ("ref.csv_bi", ref_file.read_bytes(), "application/octet-stream"),
        "hypothesis": ("hyp.csv_bi", hyp_file.read_bytes(), "application/octet-stream"),
    }


def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_submit_and_result_single_algorithm(client, sample_files):
    # Submit job for TAES dual pipeline
    res = client.post(
        "/api/v1/evaluate",
        files=sample_files,
        data=[("algorithms", "taes"), ("pipeline", "dual")],
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    assert job_id

    # Poll for completion
    deadline = time.time() + 30
    result = None
    while time.time() < deadline:
        r = client.get(f"/api/v1/evaluate/{job_id}")
        assert r.status_code == 200
        result = r.json()
        if result["status"] == "completed":
            break
        time.sleep(0.5)

    assert result is not None
    assert result["status"] == "completed"
    # Single algorithm convenience fields should be present
    assert "alpha_result" in result
    assert "beta_result" in result
    assert "parity_passed" in result


def test_websocket_progress(client, sample_files):
    res = client.post(
        "/api/v1/evaluate",
        files=sample_files,
        data=[("algorithms", "taes"), ("pipeline", "dual")],
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    with client.websocket_connect(f"/ws/{job_id}") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial"

        got_update = False
        deadline = time.time() + 15
        while time.time() < deadline:
            msg = ws.receive_json()
            if msg.get("type") in {"algorithm", "status"}:
                got_update = True
            if msg.get("type") == "status" and msg.get("status") == "completed":
                break
        assert got_update

