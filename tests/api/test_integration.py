import time
from pathlib import Path

import pytest

# Skip API tests if FastAPI/aiofiles are not installed in the environment
pytest.importorskip("fastapi")
pytest.importorskip("aiofiles")

from fastapi.testclient import TestClient  # type: ignore

from nedc_bench.api.main import app  # type: ignore
from nedc_bench.api.services.job_manager import JobManager


@pytest.fixture(scope="function")
def client(monkeypatch):
    """Create isolated TestClient with fresh job manager per test.

    CRITICAL FIX: Changed from scope="module" to scope="function" to fix race condition.

    Issue: The job_manager is a module-level singleton shared across all tests.
    When multiple tests run in parallel (pytest -n auto), they create multiple
    TestClient instances that all start worker tasks competing for jobs in the
    same shared queue. This causes jobs to fail when worker tasks get cancelled
    by other tests finishing.

    Solution: Use function scope to ensure each test gets its own isolated
    TestClient and job manager instance, preventing parallel test interference.

    Technical details:
    - Patches the singleton at its definition site (job_manager.py)
    - This ensures all imports see the patched instance
    - Each test gets a fresh JobManager with its own queue and worker
    - Prevents worker task cancellation from affecting other tests
    """
    # Create a fresh job manager instance for this test
    fresh_manager = JobManager()

    # Patch the singleton at its source - all imports will see this patched version
    monkeypatch.setattr("nedc_bench.api.services.job_manager.job_manager", fresh_manager)

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def sample_files():
    ref_file = Path("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi")
    hyp_file = Path("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi")
    assert ref_file.exists() and hyp_file.exists()
    return (ref_file, hyp_file)


@pytest.mark.xdist_group(name="api_integration")
def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.xdist_group(name="api_integration")
def test_submit_and_result_single_algorithm(client, sample_files):
    # Submit job for TAES dual pipeline
    ref_file, hyp_file = sample_files

    with open(ref_file, "rb") as f1, open(hyp_file, "rb") as f2:
        files = {
            "reference": ("ref.csv_bi", f1, "application/octet-stream"),
            "hypothesis": ("hyp.csv_bi", f2, "application/octet-stream"),
        }
        data = {"algorithms": "taes", "pipeline": "dual"}
        res = client.post("/api/v1/evaluate", files=files, data=data)
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    assert job_id

    # Poll for completion with extended timeout for robustness
    # Increased from 30s to 60s to handle slower systems (WSL2, CI/CD)
    deadline = time.time() + 60
    result = None
    while time.time() < deadline:
        r = client.get(f"/api/v1/evaluate/{job_id}")
        assert r.status_code == 200
        result = r.json()
        status = result["status"]

        if status == "completed":
            break
        if status == "failed":
            # Capture and display error for debugging
            error_msg = result.get("error", "Unknown error")
            pytest.fail(
                f"Job {job_id} failed with error: {error_msg}\n"
                f"Full result: {result}"
            )

        time.sleep(0.5)

    assert result is not None, f"No result received for job {job_id} within timeout"
    assert result["status"] == "completed", (
        f"Job {job_id} did not complete within timeout. "
        f"Final status: {result['status']}, Error: {result.get('error', 'N/A')}"
    )
    # Single algorithm convenience fields should be present
    assert "alpha_result" in result
    assert "beta_result" in result
    assert "parity_passed" in result


@pytest.mark.xdist_group(name="api_integration")
def test_websocket_progress(client, sample_files):
    ref_file, hyp_file = sample_files

    with open(ref_file, "rb") as f1, open(hyp_file, "rb") as f2:
        files = {
            "reference": ("ref.csv_bi", f1, "application/octet-stream"),
            "hypothesis": ("hyp.csv_bi", f2, "application/octet-stream"),
        }
        data = {"algorithms": "taes", "pipeline": "dual"}
        res = client.post("/api/v1/evaluate", files=files, data=data)
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    with client.websocket_connect(f"/ws/{job_id}") as ws:
        init = ws.receive_json()
        assert init["type"] == "initial"

        got_update = False
        got_completion = False
        failed_with_error = None

        # Increased timeout from 15s to 30s for robustness
        deadline = time.time() + 30
        while time.time() < deadline:
            msg = ws.receive_json()
            msg_type = msg.get("type")

            if msg_type in {"algorithm", "status"}:
                got_update = True

            if msg_type == "status":
                status = msg.get("status")
                if status == "completed":
                    got_completion = True
                    break
                if status == "failed":
                    failed_with_error = msg.get("error", "Unknown error")
                    pytest.fail(
                        f"Job {job_id} failed via websocket: {failed_with_error}\n"
                        f"Message: {msg}"
                    )

        assert got_update, f"No progress updates received for job {job_id}"
        assert got_completion, f"Job {job_id} did not complete within timeout"
