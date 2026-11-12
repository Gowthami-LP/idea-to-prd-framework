from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.alternatives import ExperimentCreate, FeasibilityCreate


def create_experiment(
    db: Database,
    project_id: str,
    data: ExperimentCreate,
) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    record = {
        "experiment_id": f"EXP-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "status": "PLANNED" if data.results is None else "COMPLETED",
        "created_at": datetime.now(timezone.utc),
    }
    db["experiments"].insert_one(record)
    record.pop("_id", None)
    return record


def get_experiments(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["experiments"].find({"project_id": project_id})
    ]


def create_feasibility_assessment(
    db: Database,
    project_id: str,
    data: FeasibilityCreate,
) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    failed_tests = [
        test for test in data.tests
        if test.get("status", "").upper() in {"FAILED", "BLOCKED"}
    ]
    record = {
        "assessment_id": f"FEAS-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "status": "FAILED" if failed_tests else "PASSED",
        "created_at": datetime.now(timezone.utc),
    }
    db["feasibility_assessments"].insert_one(record)
    record.pop("_id", None)
    return record


def get_feasibility_assessments(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["feasibility_assessments"].find({"project_id": project_id})
    ]
