from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    task_id: str | None = None
    project_id: str
    phase_id: str
    requirement_ids: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(min_length=1)
    owner: str | None = None


class TaskStatusUpdate(BaseModel):
    status: str
