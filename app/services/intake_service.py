from uuid import uuid4

from pymongo.database import Database

from app.models.project import Project
from app.schemas.project import ProjectCreate


def identify_missing_information(project_data: ProjectCreate) -> list[str]:
    """
    Identifies important information missing from the initial business idea.
    Missing fields are treated as unknowns, not as errors.
    """
    missing_information = []

    if not project_data.product_type:
        missing_information.append("product_type")
    if not project_data.sponsor:
        missing_information.append("sponsor")

    missing_information.extend(
        [
            "target_users",
            "current_workflow",
            "business_objective",
            "constraints",
        ]
    )

    return missing_information


def create_project(db: Database, project_data: ProjectCreate) -> Project:
    """Creates and persists a new project from the submitted business idea."""
    project = Project(
        project_id=f"PRJ-{uuid4().hex[:8].upper()}",
        title=project_data.title,
        business_idea=project_data.business_idea,
        product_type=project_data.product_type,
        sponsor=project_data.sponsor,
        status="INTAKE",
    )

    db["projects"].insert_one(project.model_dump())
    return project
