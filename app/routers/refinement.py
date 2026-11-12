from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.schemas.refinement import ProductBriefCreate
from app.services.refinement_service import (
    create_product_brief,
    get_product_brief,
)


router = APIRouter(prefix="/api/v1/refinement", tags=["Refinement"])


@router.post("/{project_id}", status_code=201)
def post_refinement(
    project_id: str,
    data: ProductBriefCreate,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return create_product_brief(db, project_id, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{project_id}")
def read_refinement(
    project_id: str,
    db: Database = Depends(get_db),
) -> dict:
    try:
        return get_product_brief(db, project_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
