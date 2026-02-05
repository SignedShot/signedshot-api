import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import AttestationProvider, Publisher
from app.main import app

client = TestClient(app)


def _mock_publisher(
    publisher_uuid: uuid.UUID,
    name: str = "Test Publisher",
    sandbox: bool = True,
    attestation_provider: AttestationProvider = AttestationProvider.NONE,
    attestation_bundle_id: str | None = None,
) -> Publisher:
    """Create a mock publisher."""
    return Publisher(
        id=publisher_uuid,
        name=name,
        firebase_project_id="test-project-123",
        track_devices=True,
        sandbox=sandbox,
        attestation_provider=attestation_provider,
        attestation_bundle_id=attestation_bundle_id,
        created_at=datetime.now(UTC),
    )


def test_create_publisher_success() -> None:
    """Successfully create a new publisher."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_publisher(publisher_uuid)

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
    assert data["attestation_provider"] == "none"
    assert data["attestation_bundle_id"] is None
    assert "created_at" in data


def test_create_publisher_with_attestation() -> None:
    """Create publisher with attestation configuration."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_publisher(
        publisher_uuid,
        sandbox=False,
        attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        attestation_bundle_id="io.signedshot.capture",
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
                    "sandbox": False,
                    "attestation_provider": "firebase_app_check",
                    "attestation_bundle_id": "io.signedshot.capture",
                },
            )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["sandbox"] is False
    assert data["attestation_provider"] == "firebase_app_check"
    assert data["attestation_bundle_id"] == "io.signedshot.capture"


def test_create_publisher_minimal() -> None:
    """Successfully create publisher with only required fields."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = Publisher(
        id=publisher_uuid,
        name="Minimal Publisher",
        firebase_project_id=None,
        track_devices=False,
        sandbox=True,
        attestation_provider=AttestationProvider.NONE,
        attestation_bundle_id=None,
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


# PATCH tests


def test_update_publisher_success() -> None:
    """Successfully update a publisher."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_publisher(
        publisher_uuid,
        attestation_bundle_id="io.signedshot.capture",
    )

    with (
        patch("app.api.routes.publisher.get_session") as mock_get_session,
        patch("app.api.routes.publisher.publisher_repository") as mock_repo,
        patch("app.api.routes.publisher.publisher_service") as mock_service,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_service.update = AsyncMock(return_value=mock_publisher)

        response = client.patch(
            f"/publishers/{publisher_uuid}",
            json={"attestation_bundle_id": "io.signedshot.capture"},
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["attestation_bundle_id"] == "io.signedshot.capture"


def test_update_publisher_multiple_fields() -> None:
    """Update multiple fields at once."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_publisher(
        publisher_uuid,
        sandbox=False,
        attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        attestation_bundle_id="io.signedshot.capture",
    )

    with (
        patch("app.api.routes.publisher.get_session") as mock_get_session,
        patch("app.api.routes.publisher.publisher_repository") as mock_repo,
        patch("app.api.routes.publisher.publisher_service") as mock_service,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_service.update = AsyncMock(return_value=mock_publisher)

        response = client.patch(
            f"/publishers/{publisher_uuid}",
            json={
                "sandbox": False,
                "attestation_provider": "firebase_app_check",
                "attestation_bundle_id": "io.signedshot.capture",
            },
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["sandbox"] is False
    assert data["attestation_provider"] == "firebase_app_check"
    assert data["attestation_bundle_id"] == "io.signedshot.capture"


def test_update_publisher_not_found() -> None:
    """Return 404 when publisher not found."""
    publisher_uuid = uuid.uuid4()

    with (
        patch("app.api.routes.publisher.get_session") as mock_get_session,
        patch("app.api.routes.publisher.publisher_repository") as mock_repo,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_repo.get_by_id = AsyncMock(return_value=None)

        response = client.patch(
            f"/publishers/{publisher_uuid}",
            json={"name": "New Name"},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_update_publisher_invalid_id() -> None:
    """Return 400 when publisher ID is invalid."""
    response = client.patch(
        "/publishers/not-a-uuid",
        json={"name": "New Name"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid publisher ID format"


# GET tests


def test_get_publisher_success() -> None:
    """Successfully get a publisher."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_publisher(publisher_uuid)

    with (
        patch("app.api.routes.publisher.get_session") as mock_get_session,
        patch("app.api.routes.publisher.publisher_repository") as mock_repo,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_repo.get_by_id = AsyncMock(return_value=mock_publisher)

        response = client.get(f"/publishers/{publisher_uuid}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["publisher_id"] == str(publisher_uuid)
    assert data["name"] == "Test Publisher"


def test_get_publisher_not_found() -> None:
    """Return 404 when publisher not found."""
    publisher_uuid = uuid.uuid4()

    with (
        patch("app.api.routes.publisher.get_session") as mock_get_session,
        patch("app.api.routes.publisher.publisher_repository") as mock_repo,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_repo.get_by_id = AsyncMock(return_value=None)

        response = client.get(f"/publishers/{publisher_uuid}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_publisher_invalid_id() -> None:
    """Return 400 when publisher ID is invalid."""
    response = client.get("/publishers/not-a-uuid")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid publisher ID format"
