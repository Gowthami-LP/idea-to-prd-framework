from pydantic import BaseModel, Field


class Alternative(BaseModel):
    name: str = Field(min_length=1)
    type: str
    cost: str | None = None
    fit: str | None = None
    evidence: list[str] = Field(default_factory=list)
    source: str = Field(min_length=1)


class AlternativesCreate(BaseModel):
    alternatives: list[Alternative] = Field(min_length=1)


class ExperimentCreate(BaseModel):
    hypothesis: str = Field(min_length=1)
    method: str = Field(min_length=1)
    success_criteria: list[str] = Field(min_length=1)
    failure_criteria: list[str] = Field(min_length=1)
    results: str | None = None


class FeasibilityCreate(BaseModel):
    technical: str = Field(min_length=1)
    operational: str = Field(min_length=1)
    financial: str = Field(min_length=1)
    business: str = Field(min_length=1)
    tests: list[dict[str, str]] = Field(default_factory=list)
