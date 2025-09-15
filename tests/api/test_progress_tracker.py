from __future__ import annotations

import asyncio

import pytest

from nedc_bench.api.services.progress_tracker import ProgressTracker


@pytest.mark.asyncio
async def test_progress_tracker_flow() -> None:
    pt = ProgressTracker()
    job_id = "j1"

    await pt.init_job(job_id, total_algorithms=2)
    p0 = await pt.get_progress(job_id)
    assert p0["percent_complete"] == 0.0
    assert p0["completed"] == 0
    assert p0["total"] == 2

    await pt.update_algorithm(job_id, "taes", "dual", "started")
    p1 = await pt.get_progress(job_id)
    assert p1["current_algorithm"] == "taes"
    assert p1["current_pipeline"] == "dual"

    await asyncio.sleep(0.01)  # ensure non-zero duration
    await pt.update_algorithm(job_id, "taes", "dual", "completed")
    p2 = await pt.get_progress(job_id)
    assert p2["completed"] == 1
    # start next
    await pt.update_algorithm(job_id, "dp", "beta", "started")
    await pt.update_algorithm(job_id, "dp", "beta", "completed")
    p3 = await pt.get_progress(job_id)
    assert p3["completed"] == 2
    assert p3["percent_complete"] == 100.0
