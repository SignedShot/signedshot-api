from fastapi import APIRouter, File, UploadFile, status

import signedshot

from app.schemas.validate import (
    CaptureTrustInfo,
    MediaIntegrityInfo,
    ValidationResponse,
)

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post(
    "",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid sidecar format or validation error"},
    },
)
async def validate_media(
    media: UploadFile = File(..., description="The media file (photo/video)"),
    sidecar: UploadFile = File(..., description="The sidecar JSON file"),
) -> ValidationResponse:
    """
    Validate a SignedShot media file against its sidecar.

    Upload both the media file and its corresponding sidecar JSON to verify:
    - Capture trust: JWT signature and claims verification
    - Media integrity: Content hash and signature verification
    - Capture ID match: Consistency between JWT and media integrity

    Returns detailed validation results including attestation method,
    publisher/device IDs, and any validation errors.
    """
    # Read file contents
    media_bytes = await media.read()
    sidecar_json = (await sidecar.read()).decode("utf-8")

    # Validate using the signedshot library
    result = signedshot.validate(sidecar_json, media_bytes)

    # Convert to response model
    capture_trust = result.capture_trust
    media_integrity = result.media_integrity

    return ValidationResponse(
        valid=result.valid,
        version=result.version,
        capture_trust=CaptureTrustInfo(
            signature_valid=capture_trust["signature_valid"],
            issuer=capture_trust["issuer"],
            publisher_id=capture_trust["publisher_id"],
            device_id=capture_trust["device_id"],
            capture_id=capture_trust["capture_id"],
            method=capture_trust["method"],
            issued_at=capture_trust["issued_at"],
            key_id=capture_trust.get("key_id"),
        ),
        media_integrity=MediaIntegrityInfo(
            content_hash_valid=media_integrity["content_hash_valid"],
            signature_valid=media_integrity["signature_valid"],
            capture_id_match=media_integrity["capture_id_match"],
            content_hash=media_integrity["content_hash"],
            capture_id=media_integrity["capture_id"],
            captured_at=media_integrity["captured_at"],
        ),
        error=result.error,
    )
