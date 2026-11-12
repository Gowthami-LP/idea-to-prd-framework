from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database.connection import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.intake_service import (
    create_project,
    identify_missing_information,
)


router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_new_project(
    project_data: ProjectCreate,
    db: Database = Depends(get_db),
) -> Project:
    """Accepts a business idea and stores it as a project."""
    return create_project(
        db=db,
        project_data=project_data,
    )


@router.get("/", response_model=list[ProjectResponse])
def get_all_projects(db: Database = Depends(get_db)) -> list[Project]:
    """Returns all registered projects."""
    return [
        Project.model_validate(document)
        for document in db["projects"].find()
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Database = Depends(get_db),
) -> Project:
    """Retrieves one project using its ID."""
    document = db["projects"].find_one(
        {"project_id": project_id}
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return Project.model_validate(document)


@router.get("/{project_id}/missing-information")
def get_missing_information(
    project_id: str,
    db: Database = Depends(get_db),
) -> dict[str, str | list[str]]:
    """Returns information that is not yet known for a project."""
    document = db["projects"].find_one(
        {"project_id": project_id}
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    project = Project.model_validate(document)
    missing_information = identify_missing_information(
        ProjectCreate(
            title=project.title,
            business_idea=project.business_idea,
            product_type=project.product_type,
            sponsor=project.sponsor,
        )
    )
    return {
        "project_id": project.project_id,
        "missing_information": missing_information,
    }
