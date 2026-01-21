from datetime import datetime

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    """Request to register a new device."""

    device_id: str = Field(min_length=1, max_length=255)


class DeviceRegisterResponse(BaseModel):
    """Response after successful device registration."""

    device_token: str
    created_at: datetime
