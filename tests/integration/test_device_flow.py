"""Integration tests for device registration flow."""

from fastapi import status
from fastapi.testclient import TestClient


class TestDeviceRegistration:
    """Test the complete device registration flow with real Postgres."""

    def test_register_device_success(self, integration_client: TestClient) -> None:
        """Successfully register a new device."""
        response = integration_client.post(
            "/devices/register",
            json={"external_id": "test-device-001"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "device_id" in data
        assert data["external_id"] == "test-device-001"
        assert "device_token" in data
        assert "created_at" in data

    def test_register_device_duplicate_fails(
        self, integration_client: TestClient
    ) -> None:
        """Fail to register a device with the same external_id."""
        # Register first device
        response1 = integration_client.post(
            "/devices/register",
            json={"external_id": "duplicate-device"},
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to register again with same external_id
        response2 = integration_client.post(
            "/devices/register",
            json={"external_id": "duplicate-device"},
        )
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert response2.json()["detail"] == "Device already registered"

    def test_registered_device_token_is_valid(
        self, integration_client: TestClient
    ) -> None:
        """Verify that a registered device token can be used for capture sessions."""
        # Register a device
        register_response = integration_client.post(
            "/devices/register",
            json={"external_id": "session-test-device"},
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        device_token = register_response.json()["device_token"]

        # Use the token to create a capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        assert "nonce" in session_response.json()
        assert "capture_id" in session_response.json()
