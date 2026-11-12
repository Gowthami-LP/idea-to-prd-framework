from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceCreate(BaseModel):
    """Validates evidence submitted for a project."""

    project_id: str
    claim: str = Field(min_length=5)
    evidence_type: str
    source: str = Field(min_length=1)
    evidence_date: datetime
    limitations: list[str] = Field(default_factory=list)


class EvidenceUpdate(BaseModel):
    """Editable evidence fields; source and evidence date are immutable."""

    model_config = ConfigDict(extra="forbid")

    claim: str | None = Field(default=None, min_length=5)
    evidence_type: str | None = None
    limitations: list[str] | None = None

    @model_validator(mode="after")
    def require_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one editable field is required")
        return self


class EvidenceResponse(BaseModel):
    """Evidence returned by the API, including its provenance."""

    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    project_id: str
    claim: str
    evidence_type: str
    source: str
    evidence_date: datetime
    limitations: list[str] = Field(default_factory=list)
