import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import Device
from app.main import app

client = TestClient(app)


def test_create_device_success() -> None:
    """Successfully create a new device."""
    device_uuid = uuid.uuid4()
    publisher_uuid = uuid.uuid4()
    mock_device = Device(
        id=device_uuid,
        publisher_id=publisher_uuid,
        external_id="test-device-123",
        token_hash="hashed_token",
        created_at=datetime.now(UTC),
    )

    with patch("app.api.routes.device.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.device.device_service") as mock_service:
            mock_service.create = AsyncMock(
                return_value=(mock_device, "plain_token_abc123")
            )

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

    with patch("app.api.routes.device.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.device.device_service") as mock_service:
            mock_service.create = AsyncMock(
                side_effect=EntityAlreadyExistsError("Device", "existing-device")
            )

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

    with patch("app.api.routes.device.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.routes.device.device_service") as mock_service:
            # First device for publisher 1
            mock_service.create = AsyncMock(
                return_value=(mock_device_1, "token_1")
            )
            response_1 = client.post(
                "/devices",
                json={"external_id": shared_external_id},
                headers={"X-Publisher-ID": str(publisher_uuid_1)},
            )

            # Second device for publisher 2 with same external_id
            mock_service.create = AsyncMock(
                return_value=(mock_device_2, "token_2")
            )
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
