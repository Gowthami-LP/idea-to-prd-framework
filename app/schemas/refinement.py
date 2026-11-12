from pydantic import BaseModel, Field


class Goal(BaseModel):
    description: str = Field(min_length=1)
    baseline: float | None = None
    target: float | None = None
    source: str | None = None
    owner: str | None = None


class Persona(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    needs: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


class ProductBriefCreate(BaseModel):
    problem: str = Field(min_length=1)
    target_users: list[str] = Field(min_length=1)
    primary_outcome: str = Field(min_length=1)
    goals: list[Goal] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
