"""Integration tests for capture session and trust token flow."""

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestCaptureFlow:
    """Test the complete capture flow with real Postgres and Redis."""

    @pytest.fixture
    def registered_device(self, integration_client: TestClient) -> dict:
        """Register a device and return its credentials."""
        response = integration_client.post(
            "/devices/register",
            json={"external_id": "capture-test-device"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    def test_create_capture_session(
        self, integration_client: TestClient, registered_device: dict
    ) -> None:
        """Create a capture session with a valid device token."""
        response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {registered_device['device_token']}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "nonce" in data
        assert "capture_id" in data
        assert "expires_at" in data

    def test_create_capture_session_invalid_token(
        self, integration_client: TestClient
    ) -> None:
        """Fail to create session with invalid device token."""
        response = integration_client.post(
            "/capture/session",
            headers={"Authorization": "Bearer invalid-token-12345"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid device token"

    def test_create_capture_session_missing_token(
        self, integration_client: TestClient
    ) -> None:
        """Fail to create session without device token."""
        response = integration_client.post("/capture/session")

        # HTTPBearer returns 401 when token is missing (403 is for invalid token format)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_exchange_nonce_for_trust_token(
        self, integration_client: TestClient, registered_device: dict
    ) -> None:
        """Exchange a valid nonce for a trust JWT."""
        # Create a capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {registered_device['device_token']}"},
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        session_data = session_response.json()

        # Exchange nonce for JWT
        trust_response = integration_client.post(
            "/capture/trust",
            json={"nonce": session_data["nonce"]},
        )

        assert trust_response.status_code == status.HTTP_200_OK
        trust_data = trust_response.json()

        assert "trust_token" in trust_data

        # Verify the JWT structure (without signature verification)
        token = trust_data["trust_token"]
        unverified = jwt.decode(token, options={"verify_signature": False})

        assert unverified["capture_id"] == session_data["capture_id"]
        assert unverified["device_id"] == registered_device["device_id"]
        assert "iat" in unverified

    def test_nonce_consumed_after_use(
        self, integration_client: TestClient, registered_device: dict
    ) -> None:
        """Verify nonce can only be used once."""
        # Create a capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {registered_device['device_token']}"},
        )
        session_data = session_response.json()

        # First use - should succeed
        first_response = integration_client.post(
            "/capture/trust",
            json={"nonce": session_data["nonce"]},
        )
        assert first_response.status_code == status.HTTP_200_OK

        # Second use - should fail
        second_response = integration_client.post(
            "/capture/trust",
            json={"nonce": session_data["nonce"]},
        )
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert second_response.json()["detail"] == "Invalid or expired nonce"

    def test_invalid_nonce_rejected(self, integration_client: TestClient) -> None:
        """Reject requests with invalid nonce."""
        response = integration_client.post(
            "/capture/trust",
            json={"nonce": "invalid-nonce-12345"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid or expired nonce"

    def test_complete_flow(
        self, integration_client: TestClient, registered_device: dict
    ) -> None:
        """Test the complete flow from session creation to JWT generation."""
        # Step 1: Create capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {registered_device['device_token']}"},
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        session_data = session_response.json()

        # Verify session data
        assert session_data["nonce"]
        assert session_data["capture_id"]

        # Step 2: Exchange nonce for trust token
        trust_response = integration_client.post(
            "/capture/trust",
            json={"nonce": session_data["nonce"]},
        )
        assert trust_response.status_code == status.HTTP_200_OK

        # Step 3: Verify the JWT contains expected claims
        token = trust_response.json()["trust_token"]
        claims = jwt.decode(token, options={"verify_signature": False})

        assert claims["capture_id"] == session_data["capture_id"]
        assert claims["device_id"] == registered_device["device_id"]
        assert claims["iss"] == "signedshot"
        assert claims["aud"] == "signedshot"


class TestMultipleDevices:
    """Test scenarios with multiple devices."""

    def test_multiple_devices_isolated(self, integration_client: TestClient) -> None:
        """Verify that multiple devices have isolated sessions."""
        # Register two devices
        device1 = integration_client.post(
            "/devices/register",
            json={"external_id": "multi-device-001"},
        ).json()
        device2 = integration_client.post(
            "/devices/register",
            json={"external_id": "multi-device-002"},
        ).json()

        # Create sessions for each device
        session1 = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device1['device_token']}"},
        ).json()
        session2 = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device2['device_token']}"},
        ).json()

        # Sessions should have different nonces and capture IDs
        assert session1["nonce"] != session2["nonce"]
        assert session1["capture_id"] != session2["capture_id"]

        # Each device can complete its own flow
        trust1 = integration_client.post(
            "/capture/trust", json={"nonce": session1["nonce"]}
        )
        trust2 = integration_client.post(
            "/capture/trust", json={"nonce": session2["nonce"]}
        )

        assert trust1.status_code == status.HTTP_200_OK
        assert trust2.status_code == status.HTTP_200_OK

        # Verify each trust token has the correct device_id
        claims1 = jwt.decode(
            trust1.json()["trust_token"], options={"verify_signature": False}
        )
        claims2 = jwt.decode(
            trust2.json()["trust_token"], options={"verify_signature": False}
        )

        assert claims1["device_id"] == device1["device_id"]
        assert claims2["device_id"] == device2["device_id"]
