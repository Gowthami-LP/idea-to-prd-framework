from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.discovery import DiscoveryCreate, DiscoveryResponse
from app.services.discovery_service import (
    create_discovery,
    get_project_discovery,
)


router = APIRouter(
    prefix="/api/v1/discovery",
    tags=["Discovery"],
)


@router.post(
    "/{project_id}",
    response_model=DiscoveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_discovery(
    project_id: str,
    data: DiscoveryCreate,
    db: Database = Depends(get_db),
) -> DiscoveryResponse:
    try:
        return create_discovery(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{project_id}", response_model=list[DiscoveryResponse])
def get_discovery(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[DiscoveryResponse]:
    try:
        return get_project_discovery(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
