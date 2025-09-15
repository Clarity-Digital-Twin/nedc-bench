from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

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
    completed_at: Optional[datetime] = None
    pipeline: PipelineType

    # Top-level convenience fields for single-algorithm runs
    alpha_result: Optional[Dict[str, Any]] = None
    beta_result: Optional[Dict[str, Any]] = None
    parity_passed: Optional[bool] = None
    parity_report: Optional[Dict[str, Any]] = None
    alpha_time: Optional[float] = None
    beta_time: Optional[float] = None
    speedup: Optional[float] = None

    # Multi-algorithm results map
    results: Optional[Dict[str, Any]] = None

    # Error if failed
    error: Optional[str] = None
