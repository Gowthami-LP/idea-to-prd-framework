from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """
    Validates the business idea received from the API.
    """

    title: str = Field(
        min_length=3,
        max_length=200,
    )
    business_idea: str = Field(
        min_length=10,
        max_length=10000,
    )
    product_type: str | None = None
    sponsor: str | None = None


class ProjectResponse(BaseModel):
    """
    Defines the project response returned to the client.
    """

    project_id: str
    title: str
    business_idea: str
    product_type: str | None
    sponsor: str | None
    status: str

    model_config = {
        "from_attributes": True,
    }
