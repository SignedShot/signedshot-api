from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import Device
from app.main import app

client = TestClient(app)


def test_create_session_success() -> None:
    """Successfully create a capture session with valid device token."""
    mock_device = Device(
        id=1,
        device_id="test-device-123",
        token_hash="hashed_token",
        created_at=datetime.now(UTC),
    )

    with patch("app.api.dependencies.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.dependencies.device_repository") as mock_repo:
            mock_repo.get_by_token_hash = AsyncMock(return_value=mock_device)

            response = client.post(
                "/capture/session",
                headers={"Authorization": "Bearer valid_token"},
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "session_id" in data
    assert "expires_at" in data
    assert len(data["session_id"]) > 0


def test_create_session_missing_token() -> None:
    """Return 401 when Authorization header is missing."""
    response = client.post("/capture/session")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_session_invalid_token() -> None:
    """Return 401 when device token is invalid."""
    with patch("app.api.dependencies.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.dependencies.device_repository") as mock_repo:
            mock_repo.get_by_token_hash = AsyncMock(return_value=None)

            response = client.post(
                "/capture/session",
                headers={"Authorization": "Bearer invalid_token"},
            )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid device token"
