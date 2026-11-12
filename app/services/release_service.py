from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.release import GoNoGoDecision, ReleaseCreate, ReleaseResult
from app.workflow.approval_engine import validate_approver


def validate_release(release: dict) -> dict:
    errors = []
    if not release.get("verified_tasks"):
        errors.append("No verified tasks")
    if release.get("uat_status") != "PASSED":
        errors.append("UAT is not passed")
    if release.get("migration_status") not in {"NOT_REQUIRED", "PASSED"}:
        errors.append("Migration is not ready")
    if not release.get("recovery_plan"):
        errors.append("Recovery plan is missing")
    return {"ready_for_review": not errors, "errors": errors}


def create_release(db: Database, data: ReleaseCreate) -> dict:
    if db["projects"].find_one({"project_id": data.project_id}) is None:
        raise LookupError("Project not found")
    prd = db["prd_versions"].find_one(
        {
            "project_id": data.project_id,
            "version": data.prd_version,
            "status": "APPROVED",
        }
    )
    if prd is None:
        raise ValueError("Release requires an approved PRD version")
    task_ids = set(data.verified_tasks)
    tasks = list(db["tasks"].find(
        {"task_id": {"$in": list(task_ids)}, "project_id": data.project_id}
    ))
    if len(tasks) != len(task_ids) or any(task["status"] != "DONE" for task in tasks):
        raise ValueError("Every release task must be completed and verified")

    release = {
        **data.model_dump(exclude={"release_id"}),
        "release_id": data.release_id or f"REL-{uuid4().hex[:8].upper()}",
        "status": "PENDING_REVIEW",
        "go_no_go_history": [],
        "result_history": [],
        "created_at": datetime.now(timezone.utc),
    }
    release.update(validate_release(release))
    if not release["ready_for_review"]:
        release["status"] = "BLOCKED"
    db["releases"].insert_one(release)
    release.pop("_id", None)
    return release


def get_project_releases(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["releases"].find({"project_id": project_id})
    ]


def record_go_no_go(
    db: Database,
    release_id: str,
    data: GoNoGoDecision,
) -> dict:
    validate_approver(data.role)
    if data.decision not in {"GO", "NO_GO"}:
        raise ValueError("Decision must be GO or NO_GO")
    release = db["releases"].find_one({"release_id": release_id})
    if release is None:
        raise LookupError("Release not found")
    release.pop("_id", None)
    if release["prd_version"] != data.prd_version:
        raise ValueError("PRD version mismatch")
    if release["status"] == "BLOCKED" or not release["ready_for_review"]:
        raise ValueError("Release is not ready for a go/no-go decision")
    now = datetime.now(timezone.utc)
    record = {**data.model_dump(), "decided_at": now}
    new_status = "AUTHORIZED" if data.decision == "GO" else "REJECTED"
    db["releases"].update_one(
        {"release_id": release_id, "prd_version": data.prd_version},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"go_no_go_history": record},
        },
    )
    result = db["releases"].find_one({"release_id": release_id})
    result.pop("_id", None)
    return result


def record_release_result(
    db: Database,
    release_id: str,
    data: ReleaseResult,
) -> dict:
    release = db["releases"].find_one({"release_id": release_id})
    if release is None:
        raise LookupError("Release not found")
    if release["status"] != "AUTHORIZED":
        raise ValueError("Release must have a GO decision before recording results")
    if data.build_version != release["build_version"]:
        raise ValueError("Build version mismatch")
    if data.outcome not in {"SUCCEEDED", "FAILED"}:
        raise ValueError("Outcome must be SUCCEEDED or FAILED")
    if not data.health_checks:
        raise ValueError("At least one health check result is required")
    if data.outcome == "SUCCEEDED" and any(
        result.upper() != "PASSED" for result in data.health_checks
    ):
        raise ValueError("Failed health checks cannot be recorded as success")
    if data.outcome == "FAILED" and not data.recovery_action:
        raise ValueError("Recovery action is required after a failed release")

    now = datetime.now(timezone.utc)
    record = {**data.model_dump(), "recorded_at": now}
    new_status = "COMPLETED" if data.outcome == "SUCCEEDED" else "STOPPED"
    db["releases"].update_one(
        {"release_id": release_id},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"result_history": record},
        },
    )
    release = db["releases"].find_one({"release_id": release_id})
    release.pop("_id", None)
    return release
