from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.database.connection import get_db
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceCreate, EvidenceResponse, EvidenceUpdate
from app.services.evidence_service import (
    create_evidence,
    find_evidence,
    get_project_evidence,
    update_evidence,
)


router = APIRouter(
    prefix="/api/v1/evidence",
    tags=["Evidence"],
)


@router.post(
    "/",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_evidence(
    data: EvidenceCreate,
    db: Database = Depends(get_db),
) -> EvidenceResponse:
    try:
        return create_evidence(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}", response_model=list[EvidenceResponse])
def list_project_evidence(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[EvidenceResponse]:
    try:
        return get_project_evidence(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
def patch_evidence(
    evidence_id: str,
    data: EvidenceUpdate,
    db: Database = Depends(get_db),
) -> EvidenceResponse:
    try:
        evidence = update_evidence(db, evidence_id, data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence
