from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    """MongoDB document shape for a project evidence record."""

    model_config = ConfigDict(extra="ignore")

    evidence_id: str
    project_id: str
    claim: str
    evidence_type: str
    source: str
    evidence_date: datetime
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
