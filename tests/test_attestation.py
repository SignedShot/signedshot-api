"""Unit tests for attestation service."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.db.models import AttestationProvider, Publisher
from app.exceptions import AppCheckError
from app.services.attestation import (
    AttestationResult,
    InvalidPublisherConfigError,
    resolve_attestation,
)
from app.services.firebase import FirebaseAppCheckError


def _create_publisher(
    sandbox: bool = True,
    attestation_provider: AttestationProvider = AttestationProvider.NONE,
    attestation_bundle_id: str | None = None,
) -> Publisher:
    """Create a mock publisher."""
    return Publisher(
        id=uuid.uuid4(),
        name="Test Publisher",
        sandbox=sandbox,
        attestation_provider=attestation_provider,
        attestation_bundle_id=attestation_bundle_id,
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


class TestNoToken:
    """Tests when no token is provided."""

    def test_sandbox_no_token_succeeds(self) -> None:
        """Sandbox publisher without token returns sandbox mode."""
        publisher = _create_publisher(sandbox=True)
        firebase = _create_firebase_service()

        result = resolve_attestation(
            token=None,
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result == AttestationResult(method=None, attested_at=None, app_id=None)

    def test_non_sandbox_no_token_fails(self) -> None:
        """Non-sandbox publisher without token raises error."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service()

        with pytest.raises(AppCheckError, match="required for non-sandbox"):
            resolve_attestation(
                token=None,
                firebase_service=firebase,
                publisher=publisher,
            )


class TestSandboxWithToken:
    """Tests for sandbox publisher with token provided."""

    def test_sandbox_no_provider_with_token_fails(self) -> None:
        """Sandbox with no provider rejects token."""
        publisher = _create_publisher(
            sandbox=True,
            attestation_provider=AttestationProvider.NONE,
        )
        firebase = _create_firebase_service(initialized=True)

        with pytest.raises(AppCheckError, match="no attestation_provider"):
            resolve_attestation(
                token="some_token",
                firebase_service=firebase,
                publisher=publisher,
            )

    def test_sandbox_with_provider_validates_token(self) -> None:
        """Sandbox with provider validates the token."""
        publisher = _create_publisher(
            sandbox=True,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "io.foo.bar"},
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result.method == "app_check"
        assert result.app_id == "io.foo.bar"
        firebase.verify_token.assert_called_once_with("valid_token")

    def test_sandbox_with_provider_invalid_token_fails(self) -> None:
        """Sandbox with provider rejects invalid token."""
        publisher = _create_publisher(
            sandbox=True,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_error=FirebaseAppCheckError("Token expired"),
        )

        with pytest.raises(AppCheckError, match="Token expired"):
            resolve_attestation(
                token="invalid_token",
                firebase_service=firebase,
                publisher=publisher,
            )


class TestNonSandboxWithToken:
    """Tests for non-sandbox publisher with token provided."""

    def test_non_sandbox_no_provider_invalid_config(self) -> None:
        """Non-sandbox with no provider is invalid configuration."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.NONE,
        )
        firebase = _create_firebase_service(initialized=True)

        with pytest.raises(InvalidPublisherConfigError, match="must have"):
            resolve_attestation(
                token="some_token",
                firebase_service=firebase,
                publisher=publisher,
            )

    def test_non_sandbox_with_provider_validates_token(self) -> None:
        """Non-sandbox with provider validates the token."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "io.foo.bar"},
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result.method == "app_check"
        assert result.app_id == "io.foo.bar"
        assert result.attested_at is not None
        firebase.verify_token.assert_called_once_with("valid_token")

    def test_non_sandbox_with_provider_invalid_token_fails(self) -> None:
        """Non-sandbox with provider rejects invalid token."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_error=FirebaseAppCheckError("Token expired"),
        )

        with pytest.raises(AppCheckError, match="Token expired"):
            resolve_attestation(
                token="invalid_token",
                firebase_service=firebase,
                publisher=publisher,
            )

    def test_non_sandbox_firebase_not_initialized_fails(self) -> None:
        """Non-sandbox with token but Firebase not configured raises 500."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
        )
        firebase = _create_firebase_service(initialized=False)

        with pytest.raises(HTTPException) as exc_info:
            resolve_attestation(
                token="some_token",
                firebase_service=firebase,
                publisher=publisher,
            )

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()


class TestBundleIdOverride:
    """Tests for bundle_id overriding Firebase app_id."""

    def test_bundle_id_overrides_firebase_app_id(self) -> None:
        """Should use publisher's bundle_id instead of Firebase app_id."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
            attestation_bundle_id="io.signedshot.capture",
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "1:123:ios:abc"},  # Firebase returns different ID
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result.app_id == "io.signedshot.capture"

    def test_fallback_to_firebase_app_id_when_no_bundle_id(self) -> None:
        """Should use Firebase app_id when bundle_id not configured."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
            attestation_bundle_id=None,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"app_id": "io.firebase.app"},
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result.app_id == "io.firebase.app"

    def test_no_app_id_in_claims_and_no_bundle_id(self) -> None:
        """Should return None for app_id when neither is available."""
        publisher = _create_publisher(
            sandbox=False,
            attestation_provider=AttestationProvider.FIREBASE_APP_CHECK,
            attestation_bundle_id=None,
        )
        firebase = _create_firebase_service(
            initialized=True,
            verify_result={"sub": "test"},  # No app_id in claims
        )

        result = resolve_attestation(
            token="valid_token",
            firebase_service=firebase,
            publisher=publisher,
        )

        assert result.method == "app_check"
        assert result.app_id is None
