import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import Publisher
from app.main import app

client = TestClient(app)


def test_create_publisher_success() -> None:
    """Successfully create a new publisher."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = Publisher(
        id=publisher_uuid,
        name="Test Publisher",
        firebase_project_id="test-project-123",
        track_devices=True,
        sandbox=True,
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.publisher.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.publisher.publisher_service") as mock_service:
            mock_service.create = AsyncMock(return_value=mock_publisher)

            response = client.post(
                "/publishers",
                json={
                    "name": "Test Publisher",
                    "firebase_project_id": "test-project-123",
                    "track_devices": True,
                },
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["publisher_id"] == str(publisher_uuid)
    assert data["name"] == "Test Publisher"
    assert data["firebase_project_id"] == "test-project-123"
    assert data["track_devices"] is True
    assert data["sandbox"] is True
    assert "created_at" in data


def test_create_publisher_minimal() -> None:
    """Successfully create publisher with only required fields."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = Publisher(
        id=publisher_uuid,
        name="Minimal Publisher",
        firebase_project_id=None,
        track_devices=False,
        sandbox=True,
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.publisher.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.publisher.publisher_service") as mock_service:
            mock_service.create = AsyncMock(return_value=mock_publisher)

            response = client.post(
                "/publishers",
                json={"name": "Minimal Publisher"},
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["publisher_id"] == str(publisher_uuid)
    assert data["name"] == "Minimal Publisher"
    assert data["firebase_project_id"] is None
    assert data["track_devices"] is False
    assert data["sandbox"] is True


def test_create_publisher_already_exists() -> None:
    """Return 409 when publisher name already exists."""
    from app.exceptions import EntityAlreadyExistsError

    with patch("app.api.routes.publisher.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.publisher.publisher_service") as mock_service:
            mock_service.create = AsyncMock(
                side_effect=EntityAlreadyExistsError("Publisher", "Test Publisher")
            )

            response = client.post(
                "/publishers",
                json={"name": "Test Publisher"},
            )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Publisher 'Test Publisher' already exists"


def test_create_publisher_firebase_project_already_exists() -> None:
    """Return 409 when Firebase project is already registered."""
    from app.exceptions import EntityAlreadyExistsError

    with patch("app.api.routes.publisher.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.publisher.publisher_service") as mock_service:
            mock_service.create = AsyncMock(
                side_effect=EntityAlreadyExistsError("Publisher", "New Publisher")
            )

            response = client.post(
                "/publishers",
                json={
                    "name": "New Publisher",
                    "firebase_project_id": "existing-project",
                },
            )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


def test_create_publisher_duplicate_case_insensitive() -> None:
    """Return 409 when publisher name exists with different case."""
    from app.exceptions import EntityAlreadyExistsError

    with patch("app.api.routes.publisher.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.publisher.publisher_service") as mock_service:
            # Simulate case-insensitive conflict: "test publisher" exists,
            # trying to create "Test Publisher"
            mock_service.create = AsyncMock(
                side_effect=EntityAlreadyExistsError("Publisher", "Test Publisher")
            )

            response = client.post(
                "/publishers",
                json={"name": "Test Publisher"},
            )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


def test_create_publisher_empty_name() -> None:
    """Return 422 when name is empty."""
    response = client.post(
        "/publishers",
        json={"name": ""},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_publisher_missing_name() -> None:
    """Return 422 when name is missing."""
    response = client.post(
        "/publishers",
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
