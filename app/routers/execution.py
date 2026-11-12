from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.execution import VerificationCreate
from app.services.execution_service import (
    get_task_history,
    start_task,
    verify_task,
)


router = APIRouter(prefix="/api/v1/execution", tags=["Execution"])


@router.post("/tasks/{task_id}/start", status_code=201)
def post_start_task(
    task_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return start_task(db, task_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/tasks/{task_id}/verification", status_code=201)
def post_verification(
    task_id: str,
    data: VerificationCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return verify_task(db, task_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/tasks/{task_id}/history")
def read_task_history(
    task_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_task_history(db, task_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
