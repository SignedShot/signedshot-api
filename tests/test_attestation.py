"""Unit tests for attestation service."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.db.models import Publisher
from app.exceptions import AppCheckError
from app.services.attestation import AttestationResult, resolve_attestation
from app.services.firebase import FirebaseAppCheckError


def _create_publisher(sandbox: bool = True) -> Publisher:
    """Create a mock publisher."""
    return Publisher(
        id=uuid.uuid4(),
        name="Test Publisher",
        sandbox=sandbox,
        created_at=datetime.now(UTC),
    )


def _create_firebase_service(
    initialized: bool = False,
    verify_result: dict | None = None,
    verify_error: Exception | None = None,
) -> MagicMock:
    """Create a mock Firebase service."""
    mock = MagicMock()
    mock.is_initialized = initialized

    if verify_error:
        mock.verify_token.side_effect = verify_error
    elif verify_result:
        mock.verify_token.return_value = verify_result

    return mock


class TestResolveAttestationNoToken:
    """Tests for resolve_attestation when no token is provided."""

    def test_no_token_production_fails(self) -> None:
        """Should raise AppCheckError in production without token."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service()

        with pytest.raises(AppCheckError, match="required in production"):
            resolve_attestation(
                token=None,
                firebase_service=firebase,
                publisher=publisher,
                is_production=True,
            )

    def test_no_token_non_sandbox_publisher_fails(self) -> None:
        """Should raise AppCheckError for non-sandbox publisher without token."""
        publisher = _create_publisher(sandbox=False)
        firebase = _create_firebase_service()

        with pytest.raises(AppCheckError, match="required for non-sandbox"):
            resolve_attestation(
                token=None,
                firebase_service=firebase,
                publisher=publisher,
                is_production=False,
            )

    def test_no_token_sandbox_debug_succeeds(self) -> None:
        """Should return empty attestation for sandbox publisher in debug mode."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service()

        result = resolve_attestation(
            token=None,
            firebase_service=firebase,
            publisher=publisher,
            is_production=False,
        )

        assert result == AttestationResult(method=None, attested_at=None, app_id=None)


class TestResolveAttestationWithToken:
    """Tests for resolve_attestation when token is provided."""

    def test_token_firebase_not_initialized_fails(self) -> None:
        """Should raise HTTPException 500 when Firebase not configured."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service(initialized=False)

        with pytest.raises(HTTPException) as exc_info:
            resolve_attestation(
                token="some_token",
                firebase_service=firebase,
                publisher=publisher,
                is_production=False,
            )

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()

    def test_token_valid_succeeds(self) -> None:
        """Should return AttestationResult with app_check method on valid token."""
        publisher = _create_publisher(sandbox=False)
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "io.foo.bar", "sub": "test"},
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
            is_production=True,
        )

        assert result.method == "app_check"
        assert result.app_id == "io.foo.bar"
        assert result.attested_at is not None
        firebase.verify_token.assert_called_once_with("valid_token")

    def test_token_valid_no_app_id_in_claims(self) -> None:
        """Should handle claims without app_id."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"sub": "test"},  # No app_id
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
            is_production=False,
        )

        assert result.method == "app_check"
        assert result.app_id is None
        assert result.attested_at is not None

    def test_token_invalid_fails(self) -> None:
        """Should raise AppCheckError when token verification fails."""
        publisher = _create_publisher(sandbox=False)
        firebase = _create_firebase_service(
            initialized=True,
            verify_error=FirebaseAppCheckError("Token expired"),
        )

        with pytest.raises(AppCheckError, match="Token expired"):
            resolve_attestation(
                token="invalid_token",
                firebase_service=firebase,
                publisher=publisher,
                is_production=True,
            )

    def test_token_works_for_sandbox_publisher(self) -> None:
        """Should verify token even for sandbox publisher when token is provided."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "io.foo.bar"},
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
            is_production=False,
        )

        assert result.method == "app_check"
        firebase.verify_token.assert_called_once()
