from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import pytest

from nedc_bench.api.services.job_manager import JobManager
from nedc_bench.api.services import processor as processor_mod


@pytest.mark.asyncio
async def test_job_manager_basic_lifecycle() -> None:
    jm = JobManager()
    processed: list[str] = []

    async def proc(job_id: str) -> None:
        processed.append(job_id)

    # Start worker
    worker = asyncio.create_task(jm.run_worker(proc))
    assert jm.is_running() is True

    # Add a job and let worker process
    job_id = "job-1"
    await jm.add_job({"id": job_id, "created_at": datetime.utcnow(), "status": "queued"})

    # Wait until processed
    for _ in range(20):
        if job_id in processed:
            break
        await asyncio.sleep(0.05)

    assert job_id in processed

    # Shutdown
    await jm.shutdown()
    worker.cancel()
    with pytest.raises(asyncio.CancelledError):
        await worker


@pytest.mark.asyncio
async def test_process_evaluation_success(monkeypatch: Any, tmp_path: Any) -> None:
    # Prepare fake job files
    ref_file = tmp_path / "ref.csv_bi"
    hyp_file = tmp_path / "hyp.csv_bi"
    ref_file.write_text(
        "version = csv_bi_v1.0.0\npatient_id,session,channel,start_time,stop_time,label,confidence\n0,0,CH,0.0,1.0,bckg,1.0\n"
    )
    hyp_file.write_text(
        "version = csv_bi_v1.0.0\npatient_id,session,channel,start_time,stop_time,label,confidence\n0,0,CH,0.0,1.0,bckg,1.0\n"
    )

    # Use global job_manager from processor module for integration-like behavior
    jm = processor_mod.job_manager
    jm.jobs.clear()

    job_id = "job-success"
    job = {
        "id": job_id,
        "ref_path": str(ref_file),
        "hyp_path": str(hyp_file),
        "algorithms": ["taes"],
        "pipeline": "dual",
        "status": "queued",
        "created_at": datetime.utcnow(),
    }
    await jm.add_job(job)

    # Patch orchestrator to avoid heavy compute
    async def fake_eval(ref: str, hyp: str, algo: str, pipe: str) -> dict[str, Any]:
        return {
            "alpha_result": {"score": 1.0},
            "beta_result": {"score": 1.0},
            "parity_passed": True,
        }

    monkeypatch.setattr(processor_mod.async_orchestrator, "evaluate", fake_eval)

    # Stub broadcast_progress to no-op
    async def no_broadcast(job_id: str, message: dict[str, Any]) -> None:  # noqa: D401
        return None

    monkeypatch.setattr(processor_mod, "broadcast_progress", no_broadcast)

    # Run processor
    await processor_mod.process_evaluation(job_id)
    stored = await jm.get_job(job_id)
    assert stored is not None
    assert stored["status"] == "completed"
    assert "results" in stored
    assert "taes" in stored["results"]


@pytest.mark.asyncio
async def test_process_evaluation_failure(monkeypatch: Any, tmp_path: Any) -> None:
    ref = tmp_path / "ref.csv_bi"
    hyp = tmp_path / "hyp.csv_bi"
    ref.write_text(
        "version = csv_bi_v1.0.0\npatient_id,session,channel,start_time,stop_time,label,confidence\n0,0,CH,0.0,1.0,bckg,1.0\n"
    )
    hyp.write_text(
        "version = csv_bi_v1.0.0\npatient_id,session,channel,start_time,stop_time,label,confidence\n0,0,CH,0.0,1.0,bckg,1.0\n"
    )

    jm = processor_mod.job_manager
    jm.jobs.clear()
    job_id = "job-fail"
    await jm.add_job({
        "id": job_id,
        "ref_path": str(ref),
        "hyp_path": str(hyp),
        "algorithms": ["taes"],
        "pipeline": "dual",
        "status": "queued",
        "created_at": datetime.utcnow(),
    })

    async def raise_eval(*_args: Any, **_kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        raise RuntimeError("boom")

    monkeypatch.setattr(processor_mod.async_orchestrator, "evaluate", raise_eval)

    async def no_broadcast(job_id: str, message: dict[str, Any]) -> None:  # noqa: D401
        return None

    monkeypatch.setattr(processor_mod, "broadcast_progress", no_broadcast)

    await processor_mod.process_evaluation(job_id)
    stored = await jm.get_job(job_id)
    assert stored is not None
    assert stored["status"] == "failed"
    assert "error" in stored
