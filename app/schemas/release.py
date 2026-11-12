from pydantic import BaseModel, Field


class ReleaseCreate(BaseModel):
    release_id: str | None = None
    project_id: str
    prd_version: int = Field(ge=1)
    build_version: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    verified_tasks: list[str] = Field(default_factory=list)
    uat_status: str
    migration_status: str
    recovery_plan: str = ""
    rollout_strategy: str = Field(min_length=1)


class GoNoGoDecision(BaseModel):
    prd_version: int = Field(ge=1)
    decision: str
    decided_by: str = Field(min_length=1)
    role: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ReleaseResult(BaseModel):
    build_version: str = Field(min_length=1)
    health_checks: list[str] = Field(default_factory=list)
    outcome: str
    recovery_action: str | None = None
