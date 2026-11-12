from pydantic import BaseModel


class Phase(BaseModel):
    phase_id: str
    project_id: str
    prd_id: str
    title: str
    requirement_ids: list[str]
    status: str = "PLANNED"
