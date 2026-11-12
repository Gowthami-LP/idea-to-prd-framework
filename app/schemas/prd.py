from pydantic import BaseModel, Field


class RequirementCreate(BaseModel):
    requirement_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    description: str = Field(min_length=1)
    rationale: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = Field(min_length=1)
    phase_id: str | None = None


class PRDCreate(BaseModel):
    project_id: str
    problem_statement: str = ""
    product_vision: str = ""
    goals: list[str] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    requirements: list[RequirementCreate] = Field(default_factory=list)


class PRDDecision(BaseModel):
    approver_id: str = Field(min_length=1)
    approver_role: str = Field(min_length=1)
    conditions: list[str] = Field(default_factory=list)
