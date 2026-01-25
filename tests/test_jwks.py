import base64

from fastapi.testclient import TestClient

from app.services.jwk import JWKService


class TestJWKSEndpoint:
    """Tests for the JWKS endpoint."""

    def test_jwks_returns_valid_structure(self, client: TestClient) -> None:
        """JWKS endpoint should return a valid JWKS structure."""
        response = client.get("/.well-known/jwks.json")

        assert response.status_code == 200

        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) == 1

    def test_jwks_key_has_required_fields(self, client: TestClient) -> None:
        """JWKS key should have all required fields."""
        response = client.get("/.well-known/jwks.json")

        key = response.json()["keys"][0]

        assert key["kty"] == "EC"
        assert key["crv"] == "P-256"
        assert key["use"] == "sig"
        assert key["alg"] == "ES256"
        assert "kid" in key
        assert "x" in key
        assert "y" in key

    def test_jwks_coordinates_are_base64url(self, client: TestClient) -> None:
        """JWKS x and y coordinates should be valid base64url."""
        response = client.get("/.well-known/jwks.json")

        key = response.json()["keys"][0]

        # base64url decode should work (add padding if needed)
        def decode_base64url(s: str) -> bytes:
            padding = 4 - len(s) % 4
            if padding != 4:
                s += "=" * padding
            return base64.urlsafe_b64decode(s)

        x_bytes = decode_base64url(key["x"])
        y_bytes = decode_base64url(key["y"])

        # P-256 coordinates are 32 bytes each
        assert len(x_bytes) == 32
        assert len(y_bytes) == 32

    def test_jwks_kid_is_sha256_hex(self, client: TestClient) -> None:
        """JWKS kid should be a SHA256 hex string."""
        response = client.get("/.well-known/jwks.json")

        key = response.json()["keys"][0]

        # SHA256 hex is 64 characters
        assert len(key["kid"]) == 64
        # Should be valid hex
        int(key["kid"], 16)


class TestJWKService:
    """Tests for the JWK service."""

    def test_get_jwk_returns_consistent_kid(
        self, test_private_key_pem: str
    ) -> None:
        """JWK service should return consistent kid for same key."""
        service = JWKService(test_private_key_pem)

        jwk1 = service.get_jwk()
        jwk2 = service.get_jwk()

        assert jwk1.kid == jwk2.kid

    def test_get_kid_matches_jwk_kid(self, test_private_key_pem: str) -> None:
        """get_kid() should return same value as get_jwk().kid."""
        service = JWKService(test_private_key_pem)

        kid = service.get_kid()
        jwk = service.get_jwk()

        assert kid == jwk.kid

    def test_get_jwks_contains_single_key(
        self, test_private_key_pem: str
    ) -> None:
        """get_jwks() should return a response with one key."""
        service = JWKService(test_private_key_pem)

        jwks = service.get_jwks()

        assert len(jwks.keys) == 1
        assert jwks.keys[0].kid == service.get_kid()

    def test_jwk_service_caches_jwk(self, test_private_key_pem: str) -> None:
        """JWK service should cache the JWK after first creation."""
        service = JWKService(test_private_key_pem)

        jwk1 = service.get_jwk()
        jwk2 = service.get_jwk()

        # Should be the exact same object (cached)
        assert jwk1 is jwk2
