from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.planning import TaskCreate, TaskStatusUpdate
from app.services.planning_service import (
    create_task,
    generate_plan,
    get_project_phases,
    get_project_tasks,
    update_task_status,
)


planning_router = APIRouter(prefix="/api/v1/planning", tags=["Planning"])
task_router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@planning_router.post("/{prd_id}/generate", status_code=201)
def post_generate_plan(
    prd_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return generate_plan(db, prd_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@planning_router.get("/{project_id}/phases")
def read_phases(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_project_phases(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@planning_router.get("/{project_id}/tasks")
def read_tasks(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_project_tasks(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@task_router.post("/", status_code=201)
def post_task(
    data: TaskCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_task(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@task_router.patch("/{task_id}/status")
def patch_task_status(
    task_id: str,
    data: TaskStatusUpdate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return update_task_status(db, task_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
