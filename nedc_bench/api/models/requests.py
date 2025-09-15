from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class AlgorithmType(str, Enum):
    DP = "dp"
    EPOCH = "epoch"
    OVERLAP = "overlap"
    IRA = "ira"
    TAES = "taes"
    ALL = "all"


class PipelineType(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"
    DUAL = "dual"


class EvaluationRequest(BaseModel):
    """Request model for evaluation submission."""

    algorithms: List[AlgorithmType] = Field(
        default=[AlgorithmType.ALL], description="Algorithms to run",
    )
    pipeline: PipelineType = Field(
        default=PipelineType.DUAL, description="Pipeline selection",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"algorithms": ["taes"], "pipeline": "dual"}
        }
    }

