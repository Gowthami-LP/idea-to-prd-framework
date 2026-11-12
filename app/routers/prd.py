from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.prd import PRDCreate, PRDDecision
from app.services.prd_service import (
    approve_prd,
    generate_prd,
    get_latest_prd,
    get_prd_versions,
    submit_prd,
    validate_latest_prd,
)


router = APIRouter(prefix="/api/v1/prd", tags=["PRD"])


@router.post("/{project_id}/generate", status_code=201)
def post_generate_prd(
    project_id: str,
    data: PRDCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return generate_prd(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}")
def read_prd(
    project_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return get_latest_prd(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{project_id}/validate")
def get_prd_validation(
    project_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return validate_latest_prd(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{prd_id}/submit")
def post_submit_prd(
    prd_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return submit_prd(db, prd_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{prd_id}/approve")
def post_approve_prd(
    prd_id: str,
    data: PRDDecision,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return approve_prd(db, prd_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/{prd_id}/versions")
def read_prd_versions(
    prd_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_prd_versions(db, prd_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
