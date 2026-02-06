from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.settings import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(
        description="Service status. 'ok' when healthy.", examples=["ok"]
    )
    version: str = Field(
        description="Deployed application version.", examples=["v0.1.0"]
    )


@router.get("/health", response_model=HealthResponse, summary="Check API health")
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns the service status and deployed version. Use this endpoint to verify
    the API is running and to check which version is deployed.
    """
    return HealthResponse(status="ok", version=settings.app_version)
