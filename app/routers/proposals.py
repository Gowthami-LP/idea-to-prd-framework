from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.proposal import ProposalCreate, ProposalDecision
from app.services.proposal_service import (
    create_proposal,
    decide_proposal,
    get_proposals,
    submit_proposal,
)


router = APIRouter(prefix="/api/v1/proposals", tags=["Proposals"])


@router.post("/{project_id}", status_code=201)
def post_proposal(
    project_id: str,
    data: ProposalCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_proposal(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{project_id}")
def read_proposals(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_proposals(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{proposal_id}/submit")
def post_submit_proposal(
    proposal_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return submit_proposal(db, proposal_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{proposal_id}/approve")
def post_approve_proposal(
    proposal_id: str,
    data: ProposalDecision,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return decide_proposal(db, proposal_id, data, approve=True)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/{proposal_id}/reject")
def post_reject_proposal(
    proposal_id: str,
    data: ProposalDecision,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return decide_proposal(db, proposal_id, data, approve=False)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
