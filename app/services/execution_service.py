from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.execution import VerificationCreate


def start_task(db: Database, task_id: str) -> dict:
    task = db["tasks"].find_one({"task_id": task_id})
    if task is None:
        raise LookupError("Task not found")
    if task["status"] != "READY":
        raise ValueError("Task must be Ready before execution can start")

    dependencies = list(db["tasks"].find(
        {"task_id": {"$in": task.get("dependencies", [])}}
    ))
    if any(dependency["status"] != "DONE" for dependency in dependencies):
        raise ValueError("Task dependencies must be complete before execution")

    now = datetime.now(timezone.utc)
    db["tasks"].update_one(
        {"task_id": task_id},
        {"$set": {"status": "RUNNING", "updated_at": now}},
    )
    event = {
        "event_id": f"EXEC-{uuid4().hex[:8].upper()}",
        "task_id": task_id,
        "project_id": task["project_id"],
        "event": "STARTED",
        "created_at": now,
    }
    db["execution_history"].insert_one(event)
    event.pop("_id", None)
    return event


def verify_task(
    db: Database,
    task_id: str,
    data: VerificationCreate,
) -> dict:
    task = db["tasks"].find_one({"task_id": task_id})
    if task is None:
        raise LookupError("Task not found")
    if task["status"] != "RUNNING":
        raise ValueError("Task must be Running to submit verification")

    reason = "Verification criteria satisfied"
    status = "VERIFIED"
    if not data.test_results:
        status, reason = "FAILED", "No test results provided"
    elif not data.evidence_ids:
        status, reason = "FAILED", "Verification evidence missing"
    elif any(result.upper() != "PASSED" for result in data.test_results):
        status, reason = "FAILED", "One or more tests failed"
    else:
        count = db["evidence"].count_documents(
            {
                "evidence_id": {"$in": data.evidence_ids},
                "project_id": task["project_id"],
            }
        )
        if count != len(set(data.evidence_ids)):
            status, reason = "FAILED", "Evidence not found for this project"

    now = datetime.now(timezone.utc)
    verification = {
        "verification_id": f"VER-{uuid4().hex[:8].upper()}",
        "task_id": task_id,
        "project_id": task["project_id"],
        "test_results": data.test_results,
        "evidence_ids": data.evidence_ids,
        "status": status,
        "reason": reason,
        "created_at": now,
    }
    db["verifications"].insert_one(verification)
    db["tasks"].update_one(
        {"task_id": task_id},
        {
            "$set": {
                "status": "DONE" if status == "VERIFIED" else "REWORK",
                "updated_at": now,
            }
        },
    )
    db["execution_history"].insert_one(
        {
            "event_id": f"EXEC-{uuid4().hex[:8].upper()}",
            "task_id": task_id,
            "project_id": task["project_id"],
            "event": status,
            "verification_id": verification["verification_id"],
            "created_at": now,
        }
    )
    verification.pop("_id", None)
    return verification


def get_task_history(db: Database, task_id: str) -> list[dict]:
    if db["tasks"].find_one({"task_id": task_id}) is None:
        raise LookupError("Task not found")
    events = list(
        db["execution_history"].find({"task_id": task_id}).sort("created_at", 1)
    )
    verifications = list(
        db["verifications"].find({"task_id": task_id}).sort("created_at", 1)
    )
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in sorted(
            events + verifications,
            key=lambda item: item["created_at"],
        )
    ]
