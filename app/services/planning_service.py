from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.planning import TaskCreate, TaskStatusUpdate


TASK_STATUSES = {"BACKLOG", "BLOCKED", "READY", "RUNNING", "REWORK", "DONE"}
ALLOWED_TRANSITIONS = {
    "BACKLOG": {"BLOCKED", "READY"},
    "BLOCKED": {"BACKLOG"},
    "READY": {"RUNNING", "BLOCKED"},
    "RUNNING": {"REWORK", "DONE"},
    "REWORK": {"READY", "BLOCKED"},
    "DONE": set(),
}


def generate_plan(db: Database, prd_id: str) -> dict:
    prd = db["prd_versions"].find_one(
        {"prd_id": prd_id, "status": "APPROVED"},
        sort=[("version", -1)],
    )
    if prd is None:
        if db["prd_versions"].find_one({"prd_id": prd_id}) is None:
            raise LookupError("PRD not found")
        raise PermissionError("An approved PRD version is required to generate a plan")

    requirements = prd.get("requirements", [])
    groups: dict[str, list[dict]] = {}
    for requirement in requirements:
        phase_id = requirement.get("phase_id") or "PHASE-1"
        groups.setdefault(phase_id, []).append(requirement)

    now = datetime.now(timezone.utc)
    phases = []
    tasks = []
    for phase_id, phase_requirements in groups.items():
        phase = {
            "phase_id": phase_id,
            "project_id": prd["project_id"],
            "prd_id": prd_id,
            "title": f"Phase {phase_id}",
            "requirement_ids": [
                requirement["requirement_id"]
                for requirement in phase_requirements
            ],
            "status": "PLANNED",
            "created_at": now,
        }
        phases.append(phase)
        for requirement in phase_requirements:
            tasks.append(
                {
                    "task_id": f"TASK-{uuid4().hex[:8].upper()}",
                    "project_id": prd["project_id"],
                    "prd_id": prd_id,
                    "phase_id": phase_id,
                    "requirement_ids": [requirement["requirement_id"]],
                    "title": requirement["title"],
                    "description": requirement["description"],
                    "dependencies": [],
                    "acceptance_criteria": requirement["acceptance_criteria"],
                    "owner": None,
                    "status": "BACKLOG",
                    "created_at": now,
                }
            )
    if not tasks:
        raise ValueError("Approved PRD has no requirements to plan")

    db["phases"].insert_many(phases)
    db["tasks"].insert_many(tasks)
    for record in phases + tasks:
        record.pop("_id", None)
    return {
        "project_id": prd["project_id"],
        "prd_id": prd_id,
        "phases": phases,
        "tasks": tasks,
    }


def get_project_phases(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["phases"].find({"project_id": project_id})
    ]


def get_project_tasks(db: Database, project_id: str) -> list[dict]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        {key: value for key, value in item.items() if key != "_id"}
        for item in db["tasks"].find({"project_id": project_id})
    ]


def _has_dependency_cycle(task_id: str, dependencies: list[str], tasks: list[dict]) -> bool:
    graph = {
        task["task_id"]: task.get("dependencies", [])
        for task in tasks
    }
    graph[task_id] = dependencies
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(parent) for parent in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def create_task(db: Database, data: TaskCreate) -> dict:
    if db["projects"].find_one({"project_id": data.project_id}) is None:
        raise LookupError("Project not found")
    phase = db["phases"].find_one(
        {"phase_id": data.phase_id, "project_id": data.project_id}
    )
    if phase is None:
        raise LookupError("Phase not found for project")
    prd = db["prd_versions"].find_one(
        {"project_id": data.project_id, "status": "APPROVED"},
        sort=[("version", -1)],
    )
    valid_requirements = {
        item["requirement_id"] for item in (prd or {}).get("requirements", [])
    }
    if not set(data.requirement_ids).issubset(valid_requirements):
        raise ValueError("Task references requirements not in an approved PRD")
    task_id = data.task_id or f"TASK-{uuid4().hex[:8].upper()}"
    if db["tasks"].find_one({"task_id": task_id}):
        raise ValueError("Task ID already exists")

    existing_tasks = list(db["tasks"].find({"project_id": data.project_id}))
    existing_ids = {task["task_id"] for task in existing_tasks}
    if not set(data.dependencies).issubset(existing_ids):
        raise ValueError("Task dependency does not exist")
    if _has_dependency_cycle(task_id, data.dependencies, existing_tasks):
        raise ValueError("Task dependencies contain a cycle")

    task = {
        **data.model_dump(exclude={"task_id"}),
        "task_id": task_id,
        "prd_id": prd["prd_id"],
        "status": "BACKLOG",
        "created_at": datetime.now(timezone.utc),
    }
    db["tasks"].insert_one(task)
    task.pop("_id", None)
    return task


def update_task_status(
    db: Database,
    task_id: str,
    data: TaskStatusUpdate,
) -> dict:
    task = db["tasks"].find_one({"task_id": task_id})
    if task is None:
        raise LookupError("Task not found")
    new_status = data.status.upper()
    if new_status not in TASK_STATUSES:
        raise ValueError("Invalid task status")
    current = task["status"]
    if new_status not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Cannot move task from {current} to {new_status}")
    if new_status == "READY":
        dependencies = list(db["tasks"].find(
            {"task_id": {"$in": task.get("dependencies", [])}}
        ))
        if any(dep["status"] != "DONE" for dep in dependencies):
            raise ValueError("Task dependencies must be complete before Ready")
    if new_status == "DONE":
        verified = db["verifications"].find_one(
            {"task_id": task_id, "status": "VERIFIED"}
        )
        if verified is None:
            raise ValueError("Task cannot be completed without verification")

    db["tasks"].update_one(
        {"task_id": task_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
    )
    task = db["tasks"].find_one({"task_id": task_id})
    task.pop("_id", None)
    return task
