"""Integration tests for device registration flow."""

import re

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
        assert response2.json()["detail"] is not None

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

    def test_same_external_id_different_publishers(
        self, integration_client: TestClient
    ) -> None:
        """Same external_id can be used by different publishers (composite unique)."""
        # Create first publisher
        pub1_response = integration_client.post(
            "/publishers",
            json={"name": "Publisher One", "track_devices": True},
        )
        assert pub1_response.status_code == status.HTTP_201_CREATED
        publisher_id_1 = pub1_response.json()["publisher_id"]

        # Create second publisher
        pub2_response = integration_client.post(
            "/publishers",
            json={"name": "Publisher Two", "track_devices": True},
        )
        assert pub2_response.status_code == status.HTTP_201_CREATED
        publisher_id_2 = pub2_response.json()["publisher_id"]

        shared_external_id = "shared-device-id"

        # Create device for first publisher
        device1_response = integration_client.post(
            "/devices",
            json={"external_id": shared_external_id},
            headers={"X-Publisher-ID": publisher_id_1},
        )
        assert device1_response.status_code == status.HTTP_201_CREATED

        # Create device with SAME external_id for second publisher - should succeed
        device2_response = integration_client.post(
            "/devices",
            json={"external_id": shared_external_id},
            headers={"X-Publisher-ID": publisher_id_2},
        )
        assert device2_response.status_code == status.HTTP_201_CREATED

        # Verify both devices exist with same external_id but different publishers
        assert device1_response.json()["external_id"] == shared_external_id
        assert device2_response.json()["external_id"] == shared_external_id
        assert device1_response.json()["publisher_id"] == publisher_id_1
        assert device2_response.json()["publisher_id"] == publisher_id_2


class TestPublisherConstraints:
    """Test publisher database constraints."""

    def test_publisher_name_case_insensitive_unique(
        self, integration_client: TestClient
    ) -> None:
        """Publisher names should be unique case-insensitively."""
        # Create publisher with lowercase name
        response1 = integration_client.post(
            "/publishers",
            json={"name": "test publisher"},
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create publisher with same name but different case
        response2 = integration_client.post(
            "/publishers",
            json={"name": "Test Publisher"},
        )
        assert response2.status_code == status.HTTP_409_CONFLICT

        # Also try uppercase
        response3 = integration_client.post(
            "/publishers",
            json={"name": "TEST PUBLISHER"},
        )
        assert response3.status_code == status.HTTP_409_CONFLICT


class TestDatetimeFormat:
    """Test that datetime fields are serialized without microseconds."""

    # Pattern: YYYY-MM-DDTHH:MM:SSZ (no microseconds)
    ISO8601_NO_MICROSECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_device_created_at_format(self, integration_client: TestClient) -> None:
        """Device created_at should be ISO8601 without microseconds."""
        # Create publisher
        pub_response = integration_client.post(
            "/publishers",
            json={"name": "Datetime Test Publisher", "track_devices": True},
        )
        assert pub_response.status_code == status.HTTP_201_CREATED
        publisher_id = pub_response.json()["publisher_id"]

        # Create device
        device_response = integration_client.post(
            "/devices",
            json={"external_id": "datetime-test-device"},
            headers={"X-Publisher-ID": publisher_id},
        )
        assert device_response.status_code == status.HTTP_201_CREATED

        created_at = device_response.json()["created_at"]
        assert self.ISO8601_NO_MICROSECONDS.match(created_at), (
            f"created_at '{created_at}' should match format YYYY-MM-DDTHH:MM:SSZ"
        )
