from pydantic import BaseModel, Field

from app.db.models import AttestationProvider
from app.schemas.base import APIDatetime, APIResponse


class PublisherCreateRequest(BaseModel):
    """Request to create a new publisher."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Display name for the publisher",
        json_schema_extra={"example": "My Camera App"},
    )
    firebase_project_id: str | None = Field(
        default=None,
        max_length=255,
        description="Firebase project ID for App Check verification (optional for sandbox)",
        json_schema_extra={"example": "my-project-123"},
    )
    track_devices: bool = Field(
        default=False,
        description="Enable device registration and tracking for this publisher",
    )
    sandbox: bool = Field(
        default=True,
        description="Whether publisher is in sandbox/debug mode",
    )
    attestation_provider: AttestationProvider = Field(
        default=AttestationProvider.NONE,
        description="Attestation provider to use (NONE or FIREBASE_APP_CHECK)",
    )
    attestation_bundle_id: str | None = Field(
        default=None,
        max_length=255,
        description="App bundle ID for attestation (e.g., io.signedshot.capture)",
        json_schema_extra={"example": "io.signedshot.capture"},
    )


class PublisherUpdateRequest(BaseModel):
    """Request to update a publisher. All fields are optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Display name for the publisher",
    )
    firebase_project_id: str | None = Field(
        default=None,
        max_length=255,
        description="Firebase project ID for App Check verification",
    )
    track_devices: bool | None = Field(
        default=None,
        description="Enable device registration and tracking",
    )
    sandbox: bool | None = Field(
        default=None,
        description="Whether publisher is in sandbox/debug mode",
    )
    attestation_provider: AttestationProvider | None = Field(
        default=None,
        description="Attestation provider to use",
    )
    attestation_bundle_id: str | None = Field(
        default=None,
        max_length=255,
        description="App bundle ID for attestation",
    )


class PublisherCreateResponse(APIResponse):
    """Response with publisher details."""

    publisher_id: str = Field(description="Internal UUID for the publisher")
    name: str = Field(description="The publisher display name")
    firebase_project_id: str | None = Field(
        description="Firebase project ID (null for sandbox publishers)"
    )
    track_devices: bool = Field(description="Whether device tracking is enabled")
    sandbox: bool = Field(description="Whether publisher is in sandbox/debug mode")
    attestation_provider: AttestationProvider = Field(
        description="Attestation provider configured"
    )
    attestation_bundle_id: str | None = Field(
        description="App bundle ID for attestation"
    )
    created_at: APIDatetime = Field(description="When the publisher was created")
