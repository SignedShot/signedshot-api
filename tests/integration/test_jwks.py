"""Integration tests for JWKS endpoint and JWT verification."""

import jwt
from fastapi import status
from fastapi.testclient import TestClient


class TestJWKSIntegration:
    """Test JWKS endpoint with real backends."""

    def test_jwks_endpoint_returns_keys(self, integration_client: TestClient) -> None:
        """JWKS endpoint should return public keys."""
        response = integration_client.get("/.well-known/jwks.json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "keys" in data
        assert len(data["keys"]) >= 1

        key = data["keys"][0]
        assert key["kty"] == "EC"
        assert key["crv"] == "P-256"
        assert key["alg"] == "ES256"

    def test_trust_token_has_kid_matching_jwks(
        self, integration_client: TestClient
    ) -> None:
        """Trust token should have kid that matches a key in JWKS."""
        # Create publisher and device
        pub_response = integration_client.post(
            "/publishers",
            json={"name": "JWKS Test Publisher", "track_devices": True},
        )
        publisher_id = pub_response.json()["publisher_id"]

        dev_response = integration_client.post(
            "/devices",
            json={
                "external_id": "jwks-test-device",
                "public_key": "BAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0+P0A=",
            },
            headers={"X-Publisher-ID": publisher_id},
        )
        device_token = dev_response.json()["device_token"]

        # Create capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device_token}"},
        )
        nonce = session_response.json()["nonce"]

        # Exchange for trust token
        trust_response = integration_client.post(
            "/capture/trust",
            json={"nonce": nonce},
        )
        trust_token = trust_response.json()["trust_token"]

        # Get JWKS
        jwks_response = integration_client.get("/.well-known/jwks.json")
        jwks = jwks_response.json()

        # Decode JWT header (without verification)
        header = jwt.get_unverified_header(trust_token)

        # kid should match a key in JWKS
        assert "kid" in header
        jwks_kids = [key["kid"] for key in jwks["keys"]]
        assert header["kid"] in jwks_kids

    def test_trust_token_can_be_verified_with_jwks(
        self, integration_client: TestClient
    ) -> None:
        """Trust token should be verifiable using the public key from JWKS."""
        # Create publisher and device
        pub_response = integration_client.post(
            "/publishers",
            json={"name": "JWKS Verify Publisher", "track_devices": True},
        )
        publisher_id = pub_response.json()["publisher_id"]

        dev_response = integration_client.post(
            "/devices",
            json={
                "external_id": "jwks-verify-device",
                "public_key": "BAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0+P0A=",
            },
            headers={"X-Publisher-ID": publisher_id},
        )
        device_token = dev_response.json()["device_token"]

        # Create capture session
        session_response = integration_client.post(
            "/capture/session",
            headers={"Authorization": f"Bearer {device_token}"},
        )
        nonce = session_response.json()["nonce"]
        capture_id = session_response.json()["capture_id"]

        # Exchange for trust token
        trust_response = integration_client.post(
            "/capture/trust",
            json={"nonce": nonce},
        )
        trust_token = trust_response.json()["trust_token"]

        # Get JWKS
        jwks_response = integration_client.get("/.well-known/jwks.json")
        jwks = jwks_response.json()

        # Find the key by kid
        header = jwt.get_unverified_header(trust_token)
        matching_key = next(key for key in jwks["keys"] if key["kid"] == header["kid"])

        # Convert JWK to PyJWT format for verification
        from jwt import PyJWK

        jwk = PyJWK.from_dict(matching_key)

        # Verify the token
        payload = jwt.decode(
            trust_token,
            jwk.key,
            algorithms=["ES256"],
            audience="signedshot",
        )

        # Verify payload contents
        assert payload["capture_id"] == capture_id
        assert payload["iss"] == "https://dev-api.signedshot.io"
        assert payload["aud"] == "signedshot"
