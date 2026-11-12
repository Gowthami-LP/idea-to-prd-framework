from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.alternatives import AlternativesCreate


ALLOWED_ALTERNATIVE_TYPES = {
    "PROCESS_IMPROVEMENT",
    "BUY",
    "CONFIGURE",
    "INTEGRATE",
    "BUILD",
}


def compare_alternatives(
    db: Database,
    project_id: str,
    data: AlternativesCreate,
) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    for alternative in data.alternatives:
        if alternative.type not in ALLOWED_ALTERNATIVE_TYPES:
            raise ValueError("Invalid alternative type")

    record = {
        "comparison_id": f"ALT-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        "alternatives": [item.model_dump() for item in data.alternatives],
        "recommendation": "PENDING_REVIEW",
        "created_at": datetime.now(timezone.utc),
    }
    db["alternatives"].insert_one(record)
    record.pop("_id", None)
    return record


def get_alternatives(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["alternatives"].find({"project_id": project_id})
    ]
