from datetime import datetime

from pydantic import BaseModel


class CaptureSessionResponse(BaseModel):
    """Response after creating a capture session."""

    session_id: str
    expires_at: datetime
