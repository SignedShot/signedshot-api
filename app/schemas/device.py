from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    """Request to create a new device."""

    external_id: str = Field(
        min_length=1,
        max_length=255,
        description="Unique identifier for the device (e.g., hardware ID, app installation ID)",
        json_schema_extra={"example": "device-abc-123"},
    )


class DeviceCreateResponse(BaseModel):
    """Response after successful device creation."""

    device_id: str = Field(description="Internal UUID for the device")
    publisher_id: str = Field(
        description="UUID of the publisher this device belongs to"
    )
    external_id: str = Field(description="The external ID provided during registration")
    device_token: str = Field(
        description="Bearer token for authenticating capture requests. Store securely - only returned once."
    )
    created_at: datetime = Field(description="When the device was registered")
