from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.device import DeviceRegisterRequest, DeviceRegisterResponse
from app.services.device import DeviceAlreadyExistsError, device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "/register",
    response_model=DeviceRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Device already registered"},
    },
)
async def register_device(
    request: DeviceRegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> DeviceRegisterResponse:
    """
    Register a new device.

    Returns a device token that must be stored securely.
    The token is only returned once and cannot be retrieved again.
    """
    try:
        device, token = await device_service.register(session, request.device_id)
    except DeviceAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already registered",
        ) from None

    return DeviceRegisterResponse(
        device_token=token,
        created_at=device.created_at,
    )
