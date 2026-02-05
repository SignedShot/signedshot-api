"""Unit tests for Firebase App Check service."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.firebase import (
    FirebaseAppCheckError,
    FirebaseAppCheckService,
)


class TestFirebaseAppCheckServiceInitialize:
    """Tests for FirebaseAppCheckService.initialize()."""

    def test_initialize_without_credentials_returns_false(self) -> None:
        """Service should not initialize when credentials are empty."""
        service = FirebaseAppCheckService(
            project_id="test-project",
            credentials_json="",
        )
        result = service.initialize()

        assert result is False
        assert service.is_initialized is False

    def test_initialize_with_json_string_success(self) -> None:
        """Service should initialize with valid JSON credentials string."""
        fake_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        with (
            patch("app.services.firebase.credentials.Certificate") as mock_cert,
            patch("app.services.firebase.firebase_admin.initialize_app") as mock_init,
        ):
            mock_cert.return_value = MagicMock()

            service = FirebaseAppCheckService(
                project_id="test-project",
                credentials_json=json.dumps(fake_creds),
            )
            result = service.initialize()

            assert result is True
            assert service.is_initialized is True
            mock_cert.assert_called_once_with(fake_creds)
            mock_init.assert_called_once()

    def test_initialize_with_file_path_success(self, tmp_path) -> None:
        """Service should initialize with valid credentials file path."""
        fake_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
        }
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps(fake_creds))

        with (
            patch("app.services.firebase.credentials.Certificate") as mock_cert,
            patch("app.services.firebase.firebase_admin.initialize_app") as mock_init,
        ):
            mock_cert.return_value = MagicMock()

            service = FirebaseAppCheckService(
                project_id="test-project",
                credentials_json=str(creds_file),
            )
            result = service.initialize()

            assert result is True
            assert service.is_initialized is True
            mock_cert.assert_called_once_with(str(creds_file))
            mock_init.assert_called_once()

    def test_initialize_with_nonexistent_file_returns_false(self) -> None:
        """Service should not initialize when credentials file doesn't exist."""
        service = FirebaseAppCheckService(
            project_id="test-project",
            credentials_json="/nonexistent/path/credentials.json",
        )
        result = service.initialize()

        assert result is False
        assert service.is_initialized is False

    def test_initialize_already_initialized_returns_true(self) -> None:
        """Service should return True if already initialized."""
        service = FirebaseAppCheckService(
            project_id="test-project",
            credentials_json="",
        )
        service._initialized = True

        result = service.initialize()

        assert result is True

    def test_initialize_firebase_error_returns_false(self) -> None:
        """Service should return False when Firebase SDK raises an error."""
        fake_creds = {"type": "service_account", "project_id": "test"}

        with (
            patch("app.services.firebase.credentials.Certificate") as mock_cert,
            patch("app.services.firebase.firebase_admin.initialize_app") as mock_init,
        ):
            mock_cert.return_value = MagicMock()
            mock_init.side_effect = Exception("Firebase initialization failed")

            service = FirebaseAppCheckService(
                project_id="test-project",
                credentials_json=json.dumps(fake_creds),
            )
            result = service.initialize()

            assert result is False
            assert service.is_initialized is False


class TestFirebaseAppCheckServiceVerifyToken:
    """Tests for FirebaseAppCheckService.verify_token()."""

    def test_verify_token_not_initialized_raises_error(self) -> None:
        """verify_token should raise error when Firebase not initialized."""
        service = FirebaseAppCheckService(
            project_id="test-project",
            credentials_json="",
        )

        with pytest.raises(FirebaseAppCheckError, match="not initialized"):
            service.verify_token("some_token")

    def test_verify_token_success_returns_claims(self) -> None:
        """verify_token should return decoded claims on success."""
        expected_claims = {
            "app_id": "io.foo.bar",
            "sub": "test-subject",
        }

        with patch("app.services.firebase.app_check.verify_token") as mock_verify:
            mock_verify.return_value = expected_claims

            service = FirebaseAppCheckService(
                project_id="test-project",
                credentials_json="",
            )
            service._initialized = True

            result = service.verify_token("valid_token")

            assert result == expected_claims
            mock_verify.assert_called_once_with("valid_token")

    def test_verify_token_invalid_raises_error(self) -> None:
        """verify_token should raise error when token is invalid."""
        with patch("app.services.firebase.app_check.verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Token expired")

            service = FirebaseAppCheckService(
                project_id="test-project",
                credentials_json="",
            )
            service._initialized = True

            with pytest.raises(FirebaseAppCheckError, match="Invalid App Check token"):
                service.verify_token("invalid_token")
