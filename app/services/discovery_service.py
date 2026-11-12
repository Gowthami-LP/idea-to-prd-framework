from datetime import datetime, timezone
from uuid import uuid4

from pymongo.database import Database

from app.schemas.discovery import DiscoveryCreate, DiscoveryResponse


def create_discovery(
    db: Database,
    project_id: str,
    data: DiscoveryCreate,
) -> DiscoveryResponse:
    """Append a discovery record to an existing project."""
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")

    discovery = DiscoveryResponse(
        discovery_id=f"DISC-{uuid4().hex[:8].upper()}",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        **data.model_dump(),
    )
    db["discoveries"].insert_one(discovery.model_dump())
    return discovery


def get_project_discovery(
    db: Database,
    project_id: str,
) -> list[DiscoveryResponse]:
    if db["projects"].find_one({"project_id": project_id}) is None:
        raise LookupError("Project not found")
    return [
        DiscoveryResponse.model_validate(document)
        for document in db["discoveries"].find({"project_id": project_id})
    ]
