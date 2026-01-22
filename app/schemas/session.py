from datetime import datetime

from pydantic import BaseModel


class CaptureSessionResponse(BaseModel):
    """Response after creating a capture session."""

    capture_id: str
    nonce: str
    expires_at: datetime


class TrustRequest(BaseModel):
    """Request to generate a trust token."""

    nonce: str


class TrustResponse(BaseModel):
    """Response with the signed trust token."""

    trust_token: str
