from datetime import datetime

from pydantic import BaseModel, Field


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


class PublisherCreateResponse(BaseModel):
    """Response after successful publisher creation."""

    publisher_id: str = Field(description="Internal UUID for the publisher")
    name: str = Field(description="The publisher display name")
    firebase_project_id: str | None = Field(
        description="Firebase project ID (null for sandbox publishers)"
    )
    track_devices: bool = Field(description="Whether device tracking is enabled")
    sandbox: bool = Field(description="Whether publisher is in sandbox/debug mode")
    created_at: datetime = Field(description="When the publisher was created")
