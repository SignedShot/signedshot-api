"""Integration tests for device registration flow."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestDeviceRegistration:
    """Test the complete device registration flow with real Postgres."""

    @pytest.fixture
    def publisher_id(self, integration_client: TestClient) -> str:
        """Create a publisher and return its ID."""
        response = integration_client.post(
            "/publishers",
            json={"name": "Test Publisher", "track_devices": True},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()["publisher_id"]

    def test_create_device_success(
        self, integration_client: TestClient, publisher_id: str
    ) -> None:
        """Successfully create a new device."""
        response = integration_client.post(
            "/devices",
            json={"external_id": "test-device-001"},
            headers={"X-Publisher-ID": publisher_id},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "device_id" in data
        assert data["publisher_id"] == publisher_id
        assert data["external_id"] == "test-device-001"
        assert "device_token" in data
        assert "created_at" in data

    def test_create_device_duplicate_fails(
        self, integration_client: TestClient, publisher_id: str
    ) -> None:
        """Fail to create a device with the same external_id."""
        # Create first device
        response1 = integration_client.post(
            "/devices",
            json={"external_id": "duplicate-device"},
            headers={"X-Publisher-ID": publisher_id},
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create again with same external_id
        response2 = integration_client.post(
            "/devices",
            json={"external_id": "duplicate-device"},
            headers={"X-Publisher-ID": publisher_id},
        )
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert response2.json()["detail"] == "Device already registered"

    def test_device_token_is_valid(
        self, integration_client: TestClient, publisher_id: str
    ) -> None:
        """Verify that a device token can be used for capture sessions."""
        # Create a device
        create_response = integration_client.post(
            "/devices",
            json={"external_id": "session-test-device"},
            headers={"X-Publisher-ID": publisher_id},
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        device_token = create_response.json()["device_token"]

        # Use the token to create a capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device_token}"},
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        assert "nonce" in session_response.json()
        assert "capture_id" in session_response.json()
