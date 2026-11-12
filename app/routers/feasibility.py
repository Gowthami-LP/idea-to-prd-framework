from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.alternatives import ExperimentCreate, FeasibilityCreate
from app.services.feasibility_service import (
    create_experiment,
    create_feasibility_assessment,
    get_experiments,
    get_feasibility_assessments,
)


experiment_router = APIRouter(prefix="/api/v1/experiments", tags=["Experiments"])
feasibility_router = APIRouter(
    prefix="/api/v1/feasibility",
    tags=["Feasibility"],
)


@experiment_router.post("/{project_id}", status_code=201)
def post_experiment(
    project_id: str,
    data: ExperimentCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_experiment(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@experiment_router.get("/{project_id}")
def read_experiments(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_experiments(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@feasibility_router.post("/{project_id}", status_code=201)
def post_feasibility(
    project_id: str,
    data: FeasibilityCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_feasibility_assessment(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@feasibility_router.get("/{project_id}")
def read_feasibility(
    project_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    try:
        return get_feasibility_assessments(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
