from datetime import datetime

from pydantic import BaseModel, Field


class CaptureSessionResponse(BaseModel):
    """Response after creating a capture session."""

    capture_id: str = Field(description="Unique identifier for this capture")
    nonce: str = Field(
        description="One-time token to exchange for a trust token after capture"
    )
    expires_at: datetime = Field(
        description="When this session expires (must complete capture before this time)"
    )


class TrustRequest(BaseModel):
    """Request to generate a trust token."""

    nonce: str = Field(
        description="The nonce received from the capture session",
        json_schema_extra={"example": "a1b2c3d4e5f6..."},
    )


class TrustResponse(BaseModel):
    """Response with the signed trust token."""

    trust_token: str = Field(
        description="Signed JWT containing capture proof. Embed this in your media metadata."
    )
