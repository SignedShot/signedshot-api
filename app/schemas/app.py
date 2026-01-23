from datetime import datetime

from pydantic import BaseModel, Field


class AppRegisterRequest(BaseModel):
    """Request to register a new application."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Display name for the application",
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
        description="Enable device registration and tracking for this app",
    )


class AppRegisterResponse(BaseModel):
    """Response after successful app registration."""

    app_id: str = Field(description="Internal UUID for the app")
    name: str = Field(description="The app display name")
    firebase_project_id: str | None = Field(
        description="Firebase project ID (null for sandbox apps)"
    )
    track_devices: bool = Field(description="Whether device tracking is enabled")
    sandbox: bool = Field(description="Whether app is in sandbox/debug mode")
    created_at: datetime = Field(description="When the app was registered")
