from fastapi import FastAPI

from app.core.config import settings
from app.routers.alternatives import router as alternatives_router
from app.routers.discovery import router as discovery_router
from app.routers.evidence import router as evidence_router
from app.routers.execution import router as execution_router
from app.routers.feasibility import (
    experiment_router,
    feasibility_router,
)
from app.routers.outcomes import router as outcomes_router
from app.routers.planning import planning_router, task_router
from app.routers.prd import router as prd_router
from app.routers.proposals import router as proposals_router
from app.routers.projects import router as project_router
from app.routers.refinement import router as refinement_router
from app.routers.releases import router as releases_router


# Initialize FastAPI application.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A reusable framework for transforming business "
        "ideas into approved PRDs and measurable outcomes."
    ),
)

# Register project API routes.
app.include_router(project_router)
app.include_router(discovery_router)
app.include_router(evidence_router)
app.include_router(refinement_router)
app.include_router(alternatives_router)
app.include_router(experiment_router)
app.include_router(feasibility_router)
app.include_router(proposals_router)
app.include_router(prd_router)
app.include_router(planning_router)
app.include_router(task_router)
app.include_router(execution_router)
app.include_router(releases_router)
app.include_router(outcomes_router)


@app.get("/")
def root() -> dict[str, str]:
    """Returns basic application information."""
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Framework is running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Returns the application health status."""
    return {"status": "healthy"}
