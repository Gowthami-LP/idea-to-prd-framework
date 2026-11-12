from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Project(BaseModel):
    """
    MongoDB document shape for a project.
    """

    project_id: str
    title: str
    business_idea: str
    product_type: str | None = None
    sponsor: str | None = None
    status: str = "INTAKE"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
