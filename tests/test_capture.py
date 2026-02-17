import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.db.models import Capture, Device
from app.main import app
from app.services.session import SessionData

client = TestClient(app)


def test_create_session_success() -> None:
    """Successfully create a capture session with valid device token."""
    device_uuid = uuid.uuid4()
    publisher_uuid = uuid.uuid4()
    capture_uuid = uuid.uuid4()

    mock_device = Device(
        id=device_uuid,
        publisher_id=publisher_uuid,
        external_id="test-device-123",
        token_hash="hashed_token",
        created_at=datetime.now(UTC),
        attestation_method=None,  # No attestation (sandbox mode)
        public_key="dGVzdHB1YmxpY2tleQ==",
        device_public_key_fingerprint="a" * 64,
    )

    mock_capture = Capture(
        id=capture_uuid,
        publisher_id=publisher_uuid,
        device_id=device_uuid,
        created_at=datetime.now(UTC),
        completed_at=None,
    )

    with patch("app.api.dependencies.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        with patch("app.api.dependencies.device_repository") as mock_device_repo:
            mock_device_repo.get_by_token_hash = AsyncMock(return_value=mock_device)

            with patch("app.services.session.capture_repository") as mock_capture_repo:
                mock_capture_repo.create = AsyncMock(return_value=mock_capture)

                response = client.post(
                    "/capture/session",
                    headers={"Authorization": "Bearer valid_token"},
                )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "capture_id" in data
    assert "nonce" in data
    assert "expires_at" in data
    assert len(data["nonce"]) > 0


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


def test_create_trust_token_success() -> None:
    """Successfully create a trust token with valid nonce."""
    from app.services.session import get_session_service
    from app.services.trust import get_trust_service

    capture_id = str(uuid.uuid4())
    publisher_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())

    mock_session_data = SessionData(
        capture_id=capture_id,
        publisher_id=publisher_id,
        device_id=device_id,
        attestation_method=None,  # No attestation (sandbox mode)
        app_id=None,
        device_public_key_fingerprint=None,
    )

    mock_session_service = MagicMock()
    mock_session_service.consume = AsyncMock(return_value=mock_session_data)

    mock_trust_service = MagicMock()
    mock_trust_service.generate_token.return_value = "mock.jwt.token"

    app.dependency_overrides[get_session_service] = lambda: mock_session_service
    app.dependency_overrides[get_trust_service] = lambda: mock_trust_service

    try:
        with patch("app.api.routes.capture.mark_capture_completed"):
            response = client.post(
                "/capture/trust",
                json={"nonce": "valid-nonce-123"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "trust_token" in data
    assert data["trust_token"] == "mock.jwt.token"
    mock_trust_service.generate_token.assert_called_once_with(
        capture_id,
        publisher_id,
        device_id,
        method="sandbox",
        app_id=None,
        device_public_key_fingerprint=None,
    )


def test_create_trust_token_with_app_check() -> None:
    """Successfully create a trust token with app_check method for attested device."""
    from app.services.session import get_session_service
    from app.services.trust import get_trust_service

    capture_id = str(uuid.uuid4())
    publisher_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())

    mock_session_data = SessionData(
        capture_id=capture_id,
        publisher_id=publisher_id,
        device_id=device_id,
        attestation_method="app_check",  # Device was attested
        app_id="io.foo.bar",
        device_public_key_fingerprint="abc123def456",
    )

    mock_session_service = MagicMock()
    mock_session_service.consume = AsyncMock(return_value=mock_session_data)

    mock_trust_service = MagicMock()
    mock_trust_service.generate_token.return_value = "mock.jwt.token"

    app.dependency_overrides[get_session_service] = lambda: mock_session_service
    app.dependency_overrides[get_trust_service] = lambda: mock_trust_service

    try:
        with patch("app.api.routes.capture.mark_capture_completed"):
            response = client.post(
                "/capture/trust",
                json={"nonce": "valid-nonce-123"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "trust_token" in data
    assert data["trust_token"] == "mock.jwt.token"
    mock_trust_service.generate_token.assert_called_once_with(
        capture_id,
        publisher_id,
        device_id,
        method="app_check",
        app_id="io.foo.bar",
        device_public_key_fingerprint="abc123def456",
    )


def test_create_trust_token_invalid_nonce() -> None:
    """Return 400 when nonce is invalid or expired."""
    from app.services.session import get_session_service

    mock_session_service = MagicMock()
    mock_session_service.consume = AsyncMock(return_value=None)

    app.dependency_overrides[get_session_service] = lambda: mock_session_service

    try:
        response = client.post(
            "/capture/trust",
            json={"nonce": "invalid-nonce"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid or expired nonce"
