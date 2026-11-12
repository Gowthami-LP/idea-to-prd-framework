from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.alternatives import AlternativesCreate
from app.services.competitor_service import (
    compare_alternatives,
    get_alternatives,
)


router = APIRouter(prefix="/api/v1/alternatives", tags=["Alternatives"])


@router.post("/{project_id}", status_code=201)
def post_alternatives(
    project_id: str,
    data: AlternativesCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return compare_alternatives(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}")
def read_alternatives(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_alternatives(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
