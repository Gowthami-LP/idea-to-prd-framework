from pydantic import BaseModel, Field


class VerificationCreate(BaseModel):
    test_results: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
