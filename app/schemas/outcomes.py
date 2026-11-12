from typing import Literal

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    name: str = Field(min_length=1)
    unit: str | None = None
    direction: Literal["HIGHER_IS_BETTER", "LOWER_IS_BETTER"] = "HIGHER_IS_BETTER"
    baseline: float | None = None
    target: float | None = None
    source: str | None = None
    owner: str | None = None


class MeasurementCreate(BaseModel):
    metric_id: str
    actual: float
    source: str = Field(min_length=1)


class OutcomeDecisionCreate(BaseModel):
    decision: Literal["CONTINUE", "CHANGE", "STOP"]
    rationale: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)
