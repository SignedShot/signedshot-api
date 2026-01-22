from datetime import datetime

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    """Request to register a new device."""

    external_id: str = Field(
        min_length=1,
        max_length=255,
        description="Unique identifier for the device (e.g., hardware ID, app installation ID)",
        json_schema_extra={"example": "device-abc-123"},
    )


class DeviceRegisterResponse(BaseModel):
    """Response after successful device registration."""

    device_id: str = Field(description="Internal UUID for the device")
    external_id: str = Field(description="The external ID provided during registration")
    device_token: str = Field(
        description="Bearer token for authenticating capture requests. Store securely - only returned once."
    )
    created_at: datetime = Field(description="When the device was registered")
