from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.release import GoNoGoDecision, ReleaseCreate, ReleaseResult
from app.services.release_service import (
    create_release,
    get_project_releases,
    record_go_no_go,
    record_release_result,
)


router = APIRouter(prefix="/api/v1/releases", tags=["Releases"])


@router.post("/", status_code=201)
def post_release(
    data: ReleaseCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_release(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/{project_id}")
def read_releases(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_project_releases(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{release_id}/go-no-go")
def post_go_no_go(
    release_id: str,
    data: GoNoGoDecision,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return record_go_no_go(db, release_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{release_id}/record-result")
def post_release_result(
    release_id: str,
    data: ReleaseResult,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return record_release_result(db, release_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
