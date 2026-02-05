from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_device
from app.db import get_session
from app.db.models import Device
from app.exceptions import InvalidNonceError
from app.repositories.capture import mark_capture_completed
from app.schemas.session import CaptureSessionResponse, TrustRequest, TrustResponse
from app.services.session import SessionService, get_session_service
from app.services.trust import AttestationMethod, TrustService, get_trust_service

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
    db: AsyncSession = Depends(get_session),
    session_service: SessionService = Depends(get_session_service),
) -> CaptureSessionResponse:
    """
    Create a new capture session.

    Requires a valid device token in the Authorization header.
    The session is valid for a limited time and can only be used once.
    """
    result = await session_service.create(
        db,
        device.publisher_id,
        device.id,
        attestation_method=device.attestation_method,
        app_id=device.attested_app_id,
    )

    return CaptureSessionResponse(
        capture_id=result.capture_id,
        nonce=result.nonce,
        expires_at=result.expires_at,
    )


@router.post(
    "/trust",
    response_model=TrustResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid or expired nonce"},
    },
)
async def create_trust_token(
    request: TrustRequest,
    background_tasks: BackgroundTasks,
    session_service: SessionService = Depends(get_session_service),
    trust_service: TrustService = Depends(get_trust_service),
) -> TrustResponse:
    """
    Generate a trust token for a capture session.

    Consumes the session (one-time use) and returns a signed JWT.
    The JWT includes a 'method' claim indicating the attestation level:
    - sandbox: No attestation verified (testing mode)
    - app_check: Firebase App Check verified
    - app_attest: Apple App Attest verified (future)
    """
    session_data = await session_service.consume(request.nonce)

    if session_data is None:
        raise InvalidNonceError()

    # Generate the trust token
    trust_token = trust_service.generate_token(
        session_data.capture_id,
        session_data.publisher_id,
        session_data.device_id,
        method=cast("AttestationMethod", session_data.attestation_method or "sandbox"),
        app_id=session_data.app_id,
    )

    # Mark capture as completed in background
    background_tasks.add_task(mark_capture_completed, session_data.capture_id)

    return TrustResponse(trust_token=trust_token)
