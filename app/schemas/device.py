import base64

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import APIDatetime, APIResponse


class DeviceCreateRequest(BaseModel):
    """Request to create a new device."""

    external_id: str = Field(
        min_length=1,
        max_length=255,
        description="Unique identifier for the device (e.g., hardware ID, app installation ID)",
        json_schema_extra={"example": "device-abc-123"},
    )
    public_key: str = Field(
        min_length=1,
        max_length=120,
        description="Base64-encoded uncompressed EC public key (65 bytes: 0x04 + X + Y) from the device's content-signing key pair",
    )

    @field_validator("public_key")
    @classmethod
    def validate_public_key(cls, v: str) -> str:
        try:
            raw = base64.b64decode(v)
        except Exception as e:
            raise ValueError("Invalid Base64 encoding") from e
        if len(raw) != 65:
            raise ValueError(
                f"Expected 65 bytes (uncompressed EC point), got {len(raw)}"
            )
        if raw[0] != 0x04:
            raise ValueError("Expected uncompressed point format (0x04 prefix)")
        return v


class DeviceCreateResponse(APIResponse):
    """Response after successful device creation."""

    device_id: str = Field(description="Internal UUID for the device")
    publisher_id: str = Field(
        description="UUID of the publisher this device belongs to"
    )
    external_id: str = Field(description="The external ID provided during registration")
    device_token: str = Field(
        description="Bearer token for authenticating capture requests. Store securely - only returned once."
    )
    created_at: APIDatetime = Field(description="When the device was registered")
