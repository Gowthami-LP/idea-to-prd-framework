from pydantic import BaseModel


class Verification(BaseModel):
    verification_id: str
    task_id: str
    project_id: str
    test_results: list[str]
    evidence_ids: list[str]
    status: str
    reason: str
