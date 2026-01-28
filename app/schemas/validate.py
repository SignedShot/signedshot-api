from typing import Optional

from pydantic import Field

from app.schemas.base import APIResponse


class CaptureTrustInfo(APIResponse):
    """Capture trust (JWT) verification details."""

    signature_valid: bool = Field(description="Whether the JWT signature is valid")
    issuer: str = Field(description="JWT issuer")
    publisher_id: str = Field(description="Publisher ID from the token")
    device_id: str = Field(description="Device ID from the token")
    capture_id: str = Field(description="Capture ID from the token")
    method: str = Field(
        description="Attestation method: sandbox, app_check, or app_attest"
    )
    issued_at: int = Field(description="Unix timestamp when token was issued")
    key_id: Optional[str] = Field(default=None, description="Key ID used for signing")


class MediaIntegrityInfo(APIResponse):
    """Media integrity verification details."""

    content_hash_valid: bool = Field(
        description="Whether the content hash matches the media"
    )
    signature_valid: bool = Field(
        description="Whether the media integrity signature is valid"
    )
    capture_id_match: bool = Field(
        description="Whether capture ID matches between JWT and media integrity"
    )
    content_hash: str = Field(description="SHA256 hash of the media content")
    capture_id: str = Field(description="Capture ID from media integrity")
    captured_at: str = Field(description="ISO8601 timestamp of capture")


class ValidationResponse(APIResponse):
    """Response from media validation."""

    valid: bool = Field(description="Whether the media passed all validation checks")
    version: str = Field(description="Sidecar format version")
    capture_trust: CaptureTrustInfo = Field(
        description="Capture trust (JWT) verification details"
    )
    media_integrity: MediaIntegrityInfo = Field(
        description="Media integrity verification details"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if validation failed"
    )
