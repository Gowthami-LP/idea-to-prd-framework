from pymongo.database import Database

from app.models.evidence import Evidence


def create_evidence(db: Database, evidence: Evidence) -> Evidence:
    """Insert a new record without replacing conflicting evidence."""
    db["evidence"].insert_one(evidence.model_dump())
    return evidence


def get_evidence_by_id(db: Database, evidence_id: str) -> Evidence | None:
    document = db["evidence"].find_one({"evidence_id": evidence_id})
    if document is None:
        return None
    return Evidence.model_validate(document)


def get_evidence_for_project(
    db: Database,
    project_id: str,
) -> list[Evidence]:
    return [
        Evidence.model_validate(document)
        for document in db["evidence"].find({"project_id": project_id})
    ]


def update_evidence(
    db: Database,
    evidence_id: str,
    changes: dict,
) -> Evidence | None:
    if not changes:
        return get_evidence_by_id(db, evidence_id)

    result = db["evidence"].update_one(
        {"evidence_id": evidence_id},
        {"$set": changes},
    )
    if result.matched_count == 0:
        return None
    return get_evidence_by_id(db, evidence_id)
