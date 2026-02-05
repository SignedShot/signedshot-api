import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import Device, Publisher
from app.main import app

client = TestClient(app)


def _mock_sandbox_publisher(publisher_uuid: uuid.UUID) -> Publisher:
    """Create a mock publisher in sandbox mode."""
    return Publisher(
        id=publisher_uuid,
        name="Test Publisher",
        sandbox=True,
        created_at=datetime.now(UTC),
    )


def _mock_firebase_service() -> MagicMock:
    """Create a mock Firebase service (not initialized for sandbox)."""
    mock = MagicMock()
    mock.is_initialized = False
    return mock


def test_create_device_success_sandbox_debug_mode() -> None:
    """Successfully create a device in sandbox mode (debug environment)."""
    device_uuid = uuid.uuid4()
    publisher_uuid = uuid.uuid4()
    mock_device = Device(
        id=device_uuid,
        publisher_id=publisher_uuid,
        external_id="test-device-123",
        token_hash="hashed_token",
        created_at=datetime.now(UTC),
    )
    mock_publisher = _mock_sandbox_publisher(publisher_uuid)

    with (
        patch("app.api.routes.device.settings") as mock_settings,
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.device_service") as mock_service,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_settings.debug = True  # Debug mode (not production)
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_service.create = AsyncMock(
            return_value=(mock_device, "plain_token_abc123")
        )
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_firebase.return_value = _mock_firebase_service()

        response = client.post(
            "/devices",
            json={"external_id": "test-device-123"},
            headers={"X-Publisher-ID": str(publisher_uuid)},
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["device_id"] == str(device_uuid)
    assert data["publisher_id"] == str(publisher_uuid)
    assert data["external_id"] == "test-device-123"
    assert data["device_token"] == "plain_token_abc123"
    assert "created_at" in data


def test_create_device_already_exists() -> None:
    """Return 409 when device is already registered."""
    from app.exceptions import EntityAlreadyExistsError

    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_sandbox_publisher(publisher_uuid)

    with (
        patch("app.api.routes.device.settings") as mock_settings,
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.device_service") as mock_service,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_settings.debug = True  # Debug mode (not production)
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_service.create = AsyncMock(
            side_effect=EntityAlreadyExistsError("Device", "existing-device")
        )
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_firebase.return_value = _mock_firebase_service()

        response = client.post(
            "/devices",
            json={"external_id": "existing-device"},
            headers={"X-Publisher-ID": str(publisher_uuid)},
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Device 'existing-device' already exists"


def test_create_device_missing_publisher_id() -> None:
    """Return 422 when X-Publisher-ID header is missing."""
    response = client.post(
        "/devices",
        json={"external_id": "test-device-123"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_device_invalid_publisher_id() -> None:
    """Return 400 when X-Publisher-ID is not a valid UUID."""
    response = client.post(
        "/devices",
        json={"external_id": "test-device-123"},
        headers={"X-Publisher-ID": "not-a-uuid"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid publisher ID format"


def test_create_device_empty_external_id() -> None:
    """Return 422 when external_id is empty."""
    publisher_uuid = uuid.uuid4()
    response = client.post(
        "/devices",
        json={"external_id": ""},
        headers={"X-Publisher-ID": str(publisher_uuid)},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_device_same_external_id_different_publishers() -> None:
    """Successfully create devices with same external_id for different publishers."""
    device_uuid_1 = uuid.uuid4()
    device_uuid_2 = uuid.uuid4()
    publisher_uuid_1 = uuid.uuid4()
    publisher_uuid_2 = uuid.uuid4()
    shared_external_id = "shared-device-id"

    mock_device_1 = Device(
        id=device_uuid_1,
        publisher_id=publisher_uuid_1,
        external_id=shared_external_id,
        token_hash="hashed_token_1",
        created_at=datetime.now(UTC),
    )

    mock_device_2 = Device(
        id=device_uuid_2,
        publisher_id=publisher_uuid_2,
        external_id=shared_external_id,
        token_hash="hashed_token_2",
        created_at=datetime.now(UTC),
    )

    mock_publisher_1 = _mock_sandbox_publisher(publisher_uuid_1)
    mock_publisher_2 = _mock_sandbox_publisher(publisher_uuid_2)

    with (
        patch("app.api.routes.device.settings") as mock_settings,
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.device_service") as mock_service,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_settings.debug = True  # Debug mode (not production)
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_firebase.return_value = _mock_firebase_service()

        # First device for publisher 1
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher_1)
        mock_service.create = AsyncMock(return_value=(mock_device_1, "token_1"))
        response_1 = client.post(
            "/devices",
            json={"external_id": shared_external_id},
            headers={"X-Publisher-ID": str(publisher_uuid_1)},
        )

        # Second device for publisher 2 with same external_id
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher_2)
        mock_service.create = AsyncMock(return_value=(mock_device_2, "token_2"))
        response_2 = client.post(
            "/devices",
            json={"external_id": shared_external_id},
            headers={"X-Publisher-ID": str(publisher_uuid_2)},
        )

    # Both should succeed - same external_id is allowed for different publishers
    assert response_1.status_code == status.HTTP_201_CREATED
    assert response_2.status_code == status.HTTP_201_CREATED

    data_1 = response_1.json()
    data_2 = response_2.json()

    assert data_1["external_id"] == shared_external_id
    assert data_2["external_id"] == shared_external_id
    assert data_1["publisher_id"] != data_2["publisher_id"]


def test_create_device_publisher_not_found() -> None:
    """Return 404 when publisher is not found."""
    publisher_uuid = uuid.uuid4()

    with (
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_pub_repo.get_by_id = AsyncMock(return_value=None)
        mock_firebase.return_value = _mock_firebase_service()

        response = client.post(
            "/devices",
            json={"external_id": "test-device-123"},
            headers={"X-Publisher-ID": str(publisher_uuid)},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_create_device_non_sandbox_requires_app_check() -> None:
    """Return 401 when non-sandbox publisher without App Check token (even in debug mode)."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = Publisher(
        id=publisher_uuid,
        name="Production Publisher",
        sandbox=False,  # Non-sandbox mode
        created_at=datetime.now(UTC),
    )

    with (
        patch("app.api.routes.device.settings") as mock_settings,
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_settings.debug = True  # Even in debug mode, non-sandbox requires App Check
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_firebase.return_value = _mock_firebase_service()

        response = client.post(
            "/devices",
            json={"external_id": "test-device-123"},
            headers={"X-Publisher-ID": str(publisher_uuid)},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "App Check token required" in response.json()["detail"]


def test_create_device_non_sandbox_with_valid_app_check() -> None:
    """Successfully create device for non-sandbox publisher with valid App Check."""
    from app.services.firebase import get_firebase_service

    device_uuid = uuid.uuid4()
    publisher_uuid = uuid.uuid4()
    mock_device = Device(
        id=device_uuid,
        publisher_id=publisher_uuid,
        external_id="test-device-123",
        token_hash="hashed_token",
        created_at=datetime.now(UTC),
    )
    mock_publisher = Publisher(
        id=publisher_uuid,
        name="Production Publisher",
        sandbox=False,  # Non-sandbox mode
        created_at=datetime.now(UTC),
    )

    mock_firebase = MagicMock()
    mock_firebase.is_initialized = True
    mock_firebase.verify_token = MagicMock(
        return_value={"app_id": "io.foo.bar", "sub": "test"}
    )

    # Use FastAPI's dependency override for proper injection
    app.dependency_overrides[get_firebase_service] = lambda: mock_firebase

    try:
        with (
            patch("app.api.routes.device.get_session") as mock_get_session,
            patch("app.api.routes.device.device_service") as mock_service,
            patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        ):
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            mock_service.create = AsyncMock(
                return_value=(mock_device, "plain_token_abc123")
            )
            mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)

            response = client.post(
                "/devices",
                json={"external_id": "test-device-123"},
                headers={
                    "X-Publisher-ID": str(publisher_uuid),
                    "X-Firebase-AppCheck": "valid_app_check_token",
                },
            )
    finally:
        # Clean up the override
        app.dependency_overrides.pop(get_firebase_service, None)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["device_id"] == str(device_uuid)
    mock_firebase.verify_token.assert_called_once_with("valid_app_check_token")


def test_create_device_production_requires_app_check() -> None:
    """Return 401 when in production environment without App Check token."""
    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_sandbox_publisher(publisher_uuid)  # Even sandbox publisher

    with (
        patch("app.api.routes.device.settings") as mock_settings,
        patch("app.api.routes.device.get_session") as mock_get_session,
        patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        patch("app.api.routes.device.get_firebase_service") as mock_firebase,
    ):
        mock_settings.debug = False  # Production mode
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)
        mock_firebase.return_value = _mock_firebase_service()

        response = client.post(
            "/devices",
            json={"external_id": "test-device-123"},
            headers={"X-Publisher-ID": str(publisher_uuid)},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "production" in response.json()["detail"].lower()


def test_create_device_token_provided_firebase_not_initialized() -> None:
    """Return 500 when App Check token provided but Firebase not configured."""
    from app.services.firebase import get_firebase_service

    publisher_uuid = uuid.uuid4()
    mock_publisher = _mock_sandbox_publisher(publisher_uuid)

    mock_firebase = MagicMock()
    mock_firebase.is_initialized = False  # Firebase not configured

    app.dependency_overrides[get_firebase_service] = lambda: mock_firebase

    try:
        with (
            patch("app.api.routes.device.get_session") as mock_get_session,
            patch("app.api.routes.device.publisher_repository") as mock_pub_repo,
        ):
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            mock_pub_repo.get_by_id = AsyncMock(return_value=mock_publisher)

            response = client.post(
                "/devices",
                json={"external_id": "test-device-123"},
                headers={
                    "X-Publisher-ID": str(publisher_uuid),
                    "X-Firebase-AppCheck": "some_token",
                },
            )
    finally:
        app.dependency_overrides.pop(get_firebase_service, None)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "not configured" in response.json()["detail"].lower()
