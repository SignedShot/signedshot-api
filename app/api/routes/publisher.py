import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.db.models import Publisher
from app.exceptions import EntityNotFoundError
from app.repositories.publisher import publisher_repository
from app.schemas.publisher import (
    PublisherCreateRequest,
    PublisherCreateResponse,
    PublisherUpdateRequest,
)
from app.services.publisher import publisher_service

router = APIRouter(prefix="/publishers", tags=["publishers"])


def _publisher_to_response(publisher: Publisher) -> PublisherCreateResponse:
    """Convert a Publisher model to a response schema."""
    return PublisherCreateResponse(
        publisher_id=str(publisher.id),
        name=publisher.name,
        firebase_project_id=publisher.firebase_project_id,
        track_devices=publisher.track_devices,
        sandbox=publisher.sandbox,
        attestation_provider=publisher.attestation_provider,
        attestation_bundle_id=publisher.attestation_bundle_id,
        created_at=publisher.created_at,
    )


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
        sandbox=request.sandbox,
        attestation_provider=request.attestation_provider,
        attestation_bundle_id=request.attestation_bundle_id,
    )

    return _publisher_to_response(publisher)


@router.patch(
    "/{publisher_id}",
    response_model=PublisherCreateResponse,
    responses={
        404: {"description": "Publisher not found"},
        409: {"description": "Conflict with existing publisher"},
    },
)
async def update_publisher(
    publisher_id: str,
    request: PublisherUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> PublisherCreateResponse:
    """
    Update a publisher.

    Only provided fields will be updated. Fields set to null in the request
    will not be modified.
    """
    try:
        pub_uuid = uuid.UUID(publisher_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid publisher ID format",
        ) from None

    publisher = await publisher_repository.get_by_id(session, str(pub_uuid))
    if publisher is None:
        raise EntityNotFoundError("Publisher", publisher_id)

    publisher = await publisher_service.update(
        session,
        publisher=publisher,
        name=request.name,
        firebase_project_id=request.firebase_project_id,
        track_devices=request.track_devices,
        sandbox=request.sandbox,
        attestation_provider=request.attestation_provider,
        attestation_bundle_id=request.attestation_bundle_id,
    )

    return _publisher_to_response(publisher)


@router.get(
    "/{publisher_id}",
    response_model=PublisherCreateResponse,
    responses={
        404: {"description": "Publisher not found"},
    },
)
async def get_publisher(
    publisher_id: str,
    session: AsyncSession = Depends(get_session),
) -> PublisherCreateResponse:
    """
    Get a publisher by ID.
    """
    try:
        pub_uuid = uuid.UUID(publisher_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid publisher ID format",
        ) from None

    publisher = await publisher_repository.get_by_id(session, str(pub_uuid))
    if publisher is None:
        raise EntityNotFoundError("Publisher", publisher_id)

    return _publisher_to_response(publisher)
