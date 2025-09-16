from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .requests import PipelineType


class EvaluationResponse(BaseModel):
    """Response for evaluation submission."""

    job_id: str = Field(description="Unique job identifier")
    status: str
    created_at: datetime
    message: str


class EvaluationResult(BaseModel):
    """Complete evaluation result for a job."""

    job_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    pipeline: PipelineType

    # Top-level convenience fields for single-algorithm runs
    alpha_result: dict[str, Any] | None = None
    beta_result: dict[str, Any] | None = None
    parity_passed: bool | None = None
    parity_report: dict[str, Any] | None = None
    alpha_time: float | None = None
    beta_time: float | None = None
    speedup: float | None = None

    # Multi-algorithm results map
    results: dict[str, Any] | None = None

    # Error if failed
    error: str | None = None
