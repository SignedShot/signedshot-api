import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.exceptions import EntityNotFoundError
from app.repositories.publisher import publisher_repository
from app.schemas.device import DeviceCreateRequest, DeviceCreateResponse
from app.services.attestation import resolve_attestation
from app.services.device import device_service
from app.services.firebase import (
    FirebaseAppCheckService,
    get_firebase_service,
)
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    response_model=DeviceCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Attestation verification failed"},
        404: {"description": "Publisher not found"},
        409: {"description": "Device already registered"},
        500: {"description": "Attestation service not configured"},
    },
)
async def create_device(
    request: DeviceCreateRequest,
    x_publisher_id: str = Header(
        ..., description="Publisher ID (from attestation token in production)"
    ),
    x_attestation_token: str | None = Header(
        None,
        description="Attestation token (required for non-sandbox publishers)",
    ),
    session: AsyncSession = Depends(get_session),
    firebase_service: FirebaseAppCheckService = Depends(get_firebase_service),
) -> DeviceCreateResponse:
    """
    Create a new device.

    Requires X-Publisher-ID header identifying the publisher.

    Attestation verification rules:
    - In production: Attestation token is always required
    - In debug mode with sandbox publisher: Attestation token is optional
    - If token is provided: it will be verified

    Returns a device token that must be stored securely.
    The token is only returned once and cannot be retrieved again.
    """
    try:
        publisher_id = uuid.UUID(x_publisher_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid publisher ID format",
        ) from None

    publisher = await publisher_repository.get_by_id(session, str(publisher_id))
    if publisher is None:
        raise EntityNotFoundError("Publisher", str(publisher_id))

    attestation = resolve_attestation(
        x_attestation_token,
        firebase_service,
        publisher,
        is_production=not settings.debug,
    )

    device, token = await device_service.create(
        session,
        publisher_id,
        request.external_id,
        attestation_method=attestation.method,
        attested_at=attestation.attested_at,
        attested_app_id=attestation.app_id,
    )

    return DeviceCreateResponse(
        device_id=str(device.id),
        publisher_id=str(device.publisher_id),
        external_id=device.external_id,
        device_token=token,
        created_at=device.created_at,
    )
