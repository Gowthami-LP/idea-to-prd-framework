from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.prd import PRDCreate, PRDDecision
from app.workflow.approval_engine import validate_approver


def validate_prd(prd: dict) -> dict:
    errors = []
    if not prd.get("problem_statement"):
        errors.append("Missing problem statement")
    if not prd.get("product_vision"):
        errors.append("Missing product vision")
    requirements = prd.get("requirements", [])
    if not requirements:
        errors.append("No requirements defined")
    for requirement in requirements:
        if not requirement.get("acceptance_criteria"):
            errors.append(
                f"{requirement['requirement_id']}: Missing acceptance criteria"
            )
        if not requirement.get("rationale"):
            errors.append(f"{requirement['requirement_id']}: Missing rationale")
    return {"is_valid": not errors, "errors": errors}


def _render_markdown(prd: dict) -> str:
    sections = [
        f"# Product Requirements Document: {prd['project_id']}",
        f"\n## Problem\n{prd['problem_statement']}",
        f"\n## Product vision\n{prd['product_vision']}",
        "\n## Goals\n" + "\n".join(f"- {goal}" for goal in prd["goals"]),
        "\n## Scope\n" + "\n".join(f"- {item}" for item in prd["scope"]),
        "\n## Non-goals\n" + "\n".join(f"- {item}" for item in prd["non_goals"]),
        "\n## Requirements",
    ]
    for requirement in prd["requirements"]:
        criteria = "\n".join(
            f"  - {criterion}"
            for criterion in requirement["acceptance_criteria"]
        )
        sections.append(
            f"\n### {requirement['requirement_id']}: {requirement['title']}\n"
            f"- Actor: {requirement['actor']}\n"
            f"- Description: {requirement['description']}\n"
            f"- Rationale: {requirement['rationale']}\n"
            f"- Priority: {requirement['priority']}\n"
            f"- Acceptance criteria:\n{criteria}"
        )
    return "\n".join(sections)


def generate_prd(db: Database, project_id: str, data: PRDCreate) -> dict:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    if data.project_id != project_id:
        raise ValueError("PRD project_id must match the request path")

    approved_proposal = db["proposals"].find_one(
        {"project_id": project_id, "status": "APPROVED"},
        sort=[("updated_at", -1)],
    )
    if approved_proposal is None:
        raise PermissionError("An approved proposal is required to generate a PRD")
    approved_scope = set(approved_proposal.get("approval_history", [{}])[-1].get(
        "approved_scope",
        [],
    ))
    if not set(data.scope).issubset(approved_scope):
        raise PermissionError("PRD scope exceeds the approved proposal scope")

    previous = db["prd_versions"].find_one(
        {"project_id": project_id},
        sort=[("version", -1)],
    )
    prd_id = previous["prd_id"] if previous else f"PRD-{uuid4().hex[:8].upper()}"
    version = previous["version"] + 1 if previous else 1
    now = datetime.now(timezone.utc)
    prd = {
        "prd_id": prd_id,
        "project_id": project_id,
        "proposal_id": approved_proposal["proposal_id"],
        "proposal_version": approved_proposal["version"],
        **data.model_dump(),
        "version": version,
        "status": "DRAFT",
        "created_at": now,
        "updated_at": now,
    }
    prd["validation"] = validate_prd(prd)
    prd["markdown"] = _render_markdown(prd)
    db["prd_versions"].insert_one(prd)
    prd.pop("_id", None)
    return prd


def get_latest_prd(db: Database, project_id: str) -> dict:
    prd = db["prd_versions"].find_one(
        {"project_id": project_id},
        sort=[("version", -1)],
    )
    if prd is None:
        raise LookupError("PRD not found")
    prd.pop("_id", None)
    return prd


def get_prd(db: Database, prd_id: str) -> dict:
    prd = db["prd_versions"].find_one(
        {"prd_id": prd_id},
        sort=[("version", -1)],
    )
    if prd is None:
        raise LookupError("PRD not found")
    prd.pop("_id", None)
    return prd


def validate_latest_prd(db: Database, project_id: str) -> dict:
    prd = get_latest_prd(db, project_id)
    return {"prd_id": prd["prd_id"], "version": prd["version"], **validate_prd(prd)}


def get_prd_versions(db: Database, prd_id: str) -> list[dict]:
    if db["prd_versions"].find_one({"prd_id": prd_id}) is None:
        raise LookupError("PRD not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["prd_versions"].find(
            {"prd_id": prd_id},
            sort=[("version", 1)],
        )
    ]


def submit_prd(db: Database, prd_id: str) -> dict:
    prd = get_prd(db, prd_id)
    if prd["status"] != "DRAFT":
        raise ValueError("Only draft PRDs can be submitted")
    validation = validate_prd(prd)
    if not validation["is_valid"]:
        raise ValueError("PRD is invalid: " + "; ".join(validation["errors"]))
    db["prd_versions"].update_one(
        {"prd_id": prd_id, "version": prd["version"]},
        {"$set": {"status": "SUBMITTED", "updated_at": datetime.now(timezone.utc)}},
    )
    return get_prd(db, prd_id)


def approve_prd(
    db: Database,
    prd_id: str,
    decision: PRDDecision,
) -> dict:
    validate_approver(decision.approver_role)
    prd = get_prd(db, prd_id)
    if prd["status"] != "SUBMITTED":
        raise ValueError("PRD is not awaiting approval")
    now = datetime.now(timezone.utc)
    approval = {
        "approver_id": decision.approver_id,
        "approver_role": decision.approver_role,
        "conditions": decision.conditions,
        "approved_version": prd["version"],
        "approved_at": now,
    }
    db["prd_versions"].update_one(
        {"prd_id": prd_id, "version": prd["version"]},
        {
            "$set": {"status": "APPROVED", "updated_at": now},
            "$push": {"approval_history": approval},
        },
    )
    return get_prd(db, prd_id)
