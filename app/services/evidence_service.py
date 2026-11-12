from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.models.evidence import Evidence
from app.repositories.evidence_repository import (
    create_evidence as insert_evidence,
    get_evidence_by_id,
    get_evidence_for_project,
    update_evidence as update_evidence_record,
)
from app.schemas.evidence import EvidenceCreate, EvidenceUpdate


ALLOWED_TYPES = {
    "OBSERVED",
    "USER_REPORTED",
    "EXTERNALLY_SUPPORTED",
    "HYPOTHESIS",
    "UNKNOWN",
    "DECISION",
}


def _validate_evidence_type(evidence_type: str) -> None:
    if evidence_type not in ALLOWED_TYPES:
        raise ValueError("Invalid evidence type")


def create_evidence(db: Database, data: EvidenceCreate) -> Evidence:
    """Validate, persist, and return a new evidence record."""
    if db["projects"].find_one({"project_id": data.project_id}) is None:
        raise LookupError("Project not found")

    _validate_evidence_type(data.evidence_type)
    now = datetime.now(timezone.utc)
    evidence = Evidence(
        evidence_id=f"EVID-{uuid4().hex[:8].upper()}",
        project_id=data.project_id,
        claim=data.claim,
        evidence_type=data.evidence_type,
        source=data.source,
        evidence_date=data.evidence_date,
        limitations=data.limitations,
        created_at=now,
        updated_at=now,
    )
    return insert_evidence(db, evidence)


def get_project_evidence(db: Database, project_id: str) -> list[Evidence]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return get_evidence_for_project(db, project_id)


def update_evidence(
    db: Database,
    evidence_id: str,
    data: EvidenceUpdate,
) -> Evidence | None:
    changes = data.model_dump(exclude_unset=True)
    if "claim" in changes and changes["claim"] is None:
        raise ValueError("Claim cannot be null")
    if "evidence_type" in changes:
        if changes["evidence_type"] is None:
            raise ValueError("Evidence type cannot be null")
        _validate_evidence_type(changes["evidence_type"])
    if "limitations" in changes and changes["limitations"] is None:
        raise ValueError("Limitations cannot be null")

    if changes:
        changes["updated_at"] = datetime.now(timezone.utc)
    return update_evidence_record(db, evidence_id, changes)


def find_evidence(db: Database, evidence_id: str) -> Evidence | None:
    return get_evidence_by_id(db, evidence_id)
