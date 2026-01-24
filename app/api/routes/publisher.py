from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.publisher import PublisherCreateRequest, PublisherCreateResponse
from app.services.publisher import publisher_service

router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.post(
    "",
    response_model=PublisherCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Publisher already exists"},
    },
)
async def create_publisher(
    request: PublisherCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> PublisherCreateResponse:
    """
    Create a new publisher.

    Returns publisher details including the publisher_id needed for capture sessions.
    """
    publisher = await publisher_service.create(
        session,
        name=request.name,
        firebase_project_id=request.firebase_project_id,
        track_devices=request.track_devices,
    )

    return PublisherCreateResponse(
        publisher_id=str(publisher.id),
        name=publisher.name,
        firebase_project_id=publisher.firebase_project_id,
        track_devices=publisher.track_devices,
        sandbox=publisher.sandbox,
        created_at=publisher.created_at,
    )
