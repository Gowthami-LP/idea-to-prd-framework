from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.proposal import ProposalCreate, ProposalDecision
from app.workflow.approval_engine import validate_approver


def create_proposal(
    db: Database,
    project_id: str,
    data: ProposalCreate,
) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    now = datetime.now(timezone.utc)
    proposal = {
        "proposal_id": f"PROP-{uuid4().hex[:8].upper()}",
        "project_id": project_id,
        **data.model_dump(),
        "version": 1,
        "status": "DRAFT",
        "approval_history": [],
        "created_at": now,
        "updated_at": now,
    }
    db["proposals"].insert_one(proposal)
    proposal.pop("_id", None)
    return proposal


def get_proposals(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["proposals"].find({"project_id": project_id})
    ]


def _find_proposal(db: Database, proposal_id: str) -> dict:
    proposal = db["proposals"].find_one({"proposal_id": proposal_id})
    if proposal is None:
        raise LookupError("Proposal not found")
    proposal.pop("_id", None)
    return proposal


def submit_proposal(db: Database, proposal_id: str) -> dict:
    proposal = _find_proposal(db, proposal_id)
    if proposal["status"] != "DRAFT":
        raise ValueError("Only draft proposals can be submitted")
    db["proposals"].update_one(
        {"proposal_id": proposal_id, "version": proposal["version"]},
        {"$set": {"status": "SUBMITTED", "updated_at": datetime.now(timezone.utc)}},
    )
    return _find_proposal(db, proposal_id)


def decide_proposal(
    db: Database,
    proposal_id: str,
    decision: ProposalDecision,
    approve: bool,
) -> dict:
    validate_approver(decision.approver_role)
    proposal = _find_proposal(db, proposal_id)
    if proposal["version"] != decision.version:
        raise ValueError("Proposal version mismatch")
    if proposal["status"] != "SUBMITTED":
        raise ValueError("Proposal is not awaiting approval")
    if approve and not decision.approved_scope:
        raise ValueError("Approved scope is required")
    if approve and not set(decision.approved_scope).issubset(set(proposal["scope"])):
        raise ValueError("Approved scope must be within the proposed scope")

    now = datetime.now(timezone.utc)
    status = "APPROVED" if approve else "REJECTED"
    history = {
        "approver_id": decision.approver_id,
        "approver_role": decision.approver_role,
        "version": decision.version,
        "decision": status,
        "approved_scope": decision.approved_scope if approve else [],
        "conditions": decision.conditions,
        "reason": decision.reason,
        "decided_at": now,
    }
    db["proposals"].update_one(
        {"proposal_id": proposal_id, "version": decision.version},
        {
            "$set": {"status": status, "updated_at": now},
            "$push": {"approval_history": history},
        },
    )
    return _find_proposal(db, proposal_id)
