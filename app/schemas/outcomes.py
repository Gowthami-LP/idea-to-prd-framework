from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    name: str = Field(min_length=1)
    unit: str | None = None
    direction: str = "HIGHER_IS_BETTER"
    baseline: float | None = None
    target: float | None = None
    source: str | None = None
    owner: str | None = None


class MeasurementCreate(BaseModel):
    metric_id: str
    actual: float
    source: str = Field(min_length=1)


class OutcomeDecisionCreate(BaseModel):
    decision: str
    rationale: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)
