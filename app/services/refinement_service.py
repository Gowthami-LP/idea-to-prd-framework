from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.refinement import ProductBriefCreate


def create_product_brief(
    db: Database,
    project_id: str,
    data: ProductBriefCreate,
) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")

    record = {
        "brief_id": f"BRIEF-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "status": "DRAFT",
        "created_at": datetime.now(timezone.utc),
    }
    db["product_briefs"].insert_one(record)
    record.pop("_id", None)
    return record


def get_product_brief(db: Database, project_id: str) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    record = db["product_briefs"].find_one(
        {"project_id": project_id},
        sort=[("created_at", -1)],
    )
    if record is None:
        raise LookupError("Product brief not found")
    record.pop("_id", None)
    return record
