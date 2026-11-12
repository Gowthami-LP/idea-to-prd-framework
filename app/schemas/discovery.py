from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiscoveryCreate(BaseModel):
    """Information gathered while investigating a project."""

    target_users: list[str] = Field(default_factory=list)
    current_workflow: str | None = None
    business_objective: str | None = None
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def require_discovery_content(self):
        if not any(
            (
                self.target_users,
                self.current_workflow,
                self.business_objective,
                self.constraints,
                self.open_questions,
                self.notes,
            )
        ):
            raise ValueError("At least one discovery detail is required")
        return self


class DiscoveryResponse(DiscoveryCreate):
    """Persisted discovery record returned to API clients."""

    model_config = ConfigDict(from_attributes=True)

    discovery_id: str
    project_id: str
    created_at: datetime
