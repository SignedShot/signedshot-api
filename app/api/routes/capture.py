from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_device
from app.db.models import Device
from app.schemas.session import CaptureSessionResponse
from app.services.session import SessionService, get_session_service

router = APIRouter(prefix="/capture", tags=["capture"])


@router.post(
    "/session",
    response_model=CaptureSessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid or missing device token"},
    },
)
async def create_session(
    device: Device = Depends(get_current_device),
    session_service: SessionService = Depends(get_session_service),
) -> CaptureSessionResponse:
    """
    Create a new capture session.

    Requires a valid device token in the Authorization header.
    The session is valid for a limited time and can only be used once.
    """
    session_id, expires_at = await session_service.create(device.device_id)

    return CaptureSessionResponse(
        session_id=session_id,
        expires_at=expires_at,
    )
