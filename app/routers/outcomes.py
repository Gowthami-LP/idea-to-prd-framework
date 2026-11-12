from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.outcomes import (
    MeasurementCreate,
    MetricCreate,
    OutcomeDecisionCreate,
)
from app.services.outcome_service import (
    create_measurement,
    create_metric,
    get_metrics,
    get_outcome_report,
    record_outcome_decision,
)


router = APIRouter(prefix="/api/v1/outcomes", tags=["Outcomes"])


@router.post("/{project_id}/metrics", status_code=201)
def post_metric(
    project_id: str,
    data: MetricCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_metric(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}/metrics")
def read_metrics(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_metrics(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{project_id}/measurements", status_code=201)
def post_measurement(
    project_id: str,
    data: MeasurementCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_measurement(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}/report")
def read_outcome_report(
    project_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return get_outcome_report(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{project_id}/decision", status_code=201)
def post_outcome_decision(
    project_id: str,
    data: OutcomeDecisionCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return record_outcome_decision(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
