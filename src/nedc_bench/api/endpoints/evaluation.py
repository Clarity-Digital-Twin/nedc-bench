from __future__ import annotations

import uuid
from datetime import datetime
from typing import cast

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from nedc_bench.api.models.requests import AlgorithmType, PipelineType
from nedc_bench.api.models.responses import EvaluationResponse, EvaluationResult
from nedc_bench.api.services.file_validator import FileValidator
from nedc_bench.api.services.job_manager import job_manager
from nedc_bench.api.services.websocket_manager import broadcast_progress

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def submit_evaluation(
    reference: UploadFile = File(..., description="Reference CSV_BI file"),
    hypothesis: UploadFile = File(..., description="Hypothesis CSV_BI file"),
    algorithms: list[AlgorithmType] = Form(default=[AlgorithmType.ALL]),
    pipeline: PipelineType = Form(default=PipelineType.DUAL),
) -> EvaluationResponse:
    # Read file bytes
    ref_bytes = await reference.read()
    hyp_bytes = await hypothesis.read()

    # Basic validation
    await FileValidator.validate_csv_bi(ref_bytes, reference.filename)
    await FileValidator.validate_csv_bi(hyp_bytes, hypothesis.filename)

    job_id = str(uuid.uuid4())
    ref_path = f"/tmp/{job_id}_ref.csv_bi"
    hyp_path = f"/tmp/{job_id}_hyp.csv_bi"

    # Save asynchronously
    async with aiofiles.open(ref_path, "wb") as f:
        await f.write(ref_bytes)
    async with aiofiles.open(hyp_path, "wb") as f:
        await f.write(hyp_bytes)

    # Normalize algorithms and pipeline
    alg_list = algorithms if isinstance(algorithms, list) else [algorithms]
    alg_values = [a.value if isinstance(a, AlgorithmType) else str(a) for a in alg_list]
    pipeline_value = pipeline.value if isinstance(pipeline, PipelineType) else str(pipeline)

    job = {
        "id": job_id,
        "ref_path": ref_path,
        "hyp_path": hyp_path,
        "algorithms": alg_values,
        "pipeline": pipeline_value,
        "status": "queued",
        "created_at": datetime.utcnow(),
    }

    await job_manager.add_job(job)

    # Immediately broadcast queued state so late WS subscribers can catch up
    await broadcast_progress(
        job_id,
        {
            "type": "status",
            "status": "queued",
            "message": "Job queued",
            "job_id": job_id,
            "created_at": cast(datetime, job["created_at"]).isoformat(),
        },
    )

    return EvaluationResponse(
        job_id=job_id,
        status="queued",
        created_at=cast(datetime, job["created_at"]),
        message="Evaluation job submitted successfully",
    )


@router.get("/evaluate/{job_id}", response_model=EvaluationResult)
async def get_evaluation_result(job_id: str) -> EvaluationResult:
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Build response
    base = {
        "job_id": job["id"],
        "status": job.get("status", "queued"),
        "created_at": job.get("created_at", datetime.utcnow()),
        "completed_at": job.get("completed_at"),
        "pipeline": job.get("pipeline", PipelineType.DUAL),
        "error": job.get("error"),
    }

    # If single-algorithm run, lift fields for convenience
    results = job.get("results")
    if isinstance(results, dict) and len(results) == 1:
        _, res = next(iter(results.items()))
        base.update({
            "alpha_result": res.get("alpha_result"),
            "beta_result": res.get("beta_result"),
            "parity_passed": res.get("parity_passed"),
            "parity_report": res.get("parity_report"),
            "alpha_time": res.get("alpha_time"),
            "beta_time": res.get("beta_time"),
            "speedup": res.get("speedup"),
        })
    else:
        base["results"] = results

    return EvaluationResult(**base)


@router.get("/evaluate", response_model=list[EvaluationResult])
async def list_evaluations(
    limit: int = 10, offset: int = 0, status: str | None = None
) -> list[EvaluationResult]:
    jobs = await job_manager.list_jobs(limit, offset, status)
    out: list[EvaluationResult] = [
        EvaluationResult(
            job_id=job["id"],
            status=job.get("status", "queued"),
            created_at=job.get("created_at", datetime.utcnow()),
            completed_at=job.get("completed_at"),
            pipeline=job.get("pipeline", PipelineType.DUAL),
            results=job.get("results"),
            error=job.get("error"),
        )
        for job in jobs
    ]
    return out
