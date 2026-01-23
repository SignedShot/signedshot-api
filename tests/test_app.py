import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import App
from app.main import app

client = TestClient(app)


def test_register_app_success() -> None:
    """Successfully register a new app."""
    app_uuid = uuid.uuid4()
    mock_app = App(
        id=app_uuid,
        name="Test App",
        firebase_project_id="test-project-123",
        track_devices=True,
        sandbox=True,
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.app.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.app.app_service") as mock_service:
            mock_service.register = AsyncMock(return_value=mock_app)

            response = client.post(
                "/apps/register",
                json={
                    "name": "Test App",
                    "firebase_project_id": "test-project-123",
                    "track_devices": True,
                },
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["app_id"] == str(app_uuid)
    assert data["name"] == "Test App"
    assert data["firebase_project_id"] == "test-project-123"
    assert data["track_devices"] is True
    assert data["sandbox"] is True
    assert "created_at" in data


def test_register_app_minimal() -> None:
    """Successfully register app with only required fields."""
    app_uuid = uuid.uuid4()
    mock_app = App(
        id=app_uuid,
        name="Minimal App",
        firebase_project_id=None,
        track_devices=False,
        sandbox=True,
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.app.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.app.app_service") as mock_service:
            mock_service.register = AsyncMock(return_value=mock_app)

            response = client.post(
                "/apps/register",
                json={"name": "Minimal App"},
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["app_id"] == str(app_uuid)
    assert data["name"] == "Minimal App"
    assert data["firebase_project_id"] is None
    assert data["track_devices"] is False
    assert data["sandbox"] is True


def test_register_app_already_exists() -> None:
    """Return 409 when app name is already registered."""
    from app.services.app import AppAlreadyExistsError

    with patch("app.api.routes.app.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.app.app_service") as mock_service:
            mock_service.register = AsyncMock(
                side_effect=AppAlreadyExistsError(
                    "App with name 'Test App' already registered"
                )
            )

            response = client.post(
                "/apps/register",
                json={"name": "Test App"},
            )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "App with name 'Test App' already registered"


def test_register_app_firebase_project_already_exists() -> None:
    """Return 409 when Firebase project is already registered."""
    from app.services.app import AppAlreadyExistsError

    with patch("app.api.routes.app.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.app.app_service") as mock_service:
            mock_service.register = AsyncMock(
                side_effect=AppAlreadyExistsError(
                    "App with Firebase project 'existing-project' already registered"
                )
            )

            response = client.post(
                "/apps/register",
                json={
                    "name": "New App",
                    "firebase_project_id": "existing-project",
                },
            )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Firebase project" in response.json()["detail"]


def test_register_app_empty_name() -> None:
    """Return 422 when name is empty."""
    response = client.post(
        "/apps/register",
        json={"name": ""},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_register_app_missing_name() -> None:
    """Return 422 when name is missing."""
    response = client.post(
        "/apps/register",
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
