import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.device import DeviceCreateRequest, DeviceCreateResponse
from app.services.device import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    response_model=DeviceCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Device already registered"},
    },
)
async def create_device(
    request: DeviceCreateRequest,
    x_publisher_id: str = Header(
        ..., description="Publisher ID (from attestation token in production)"
    ),
    session: AsyncSession = Depends(get_session),
) -> DeviceCreateResponse:
    """
    Create a new device.

    Requires X-Publisher-ID header identifying the publisher.
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

    device, token = await device_service.create(
        session, publisher_id, request.external_id
    )

    return DeviceCreateResponse(
        device_id=str(device.id),
        publisher_id=str(device.publisher_id),
        external_id=device.external_id,
        device_token=token,
        created_at=device.created_at,
    )
