from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    title: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    proposed_outcome: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    alternatives_considered: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ProposalDecision(BaseModel):
    approver_id: str = Field(min_length=1)
    approver_role: str = Field(min_length=1)
    version: int = Field(ge=1)
    approved_scope: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    reason: str | None = None
