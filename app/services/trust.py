from datetime import UTC, datetime
from typing import Any, Literal

import jwt

from app.services.jwk import JWKService, get_jwk_service_singleton
from app.settings import settings

# Attestation method types
AttestationMethod = Literal["sandbox", "app_check", "app_attest"]


class TrustService:
    """Service for generating trust tokens."""

    def __init__(
        self,
        private_key: str,
        issuer: str,
        audience: str,
        jwk_service: JWKService,
    ) -> None:
        self._private_key = private_key
        self._issuer = issuer
        self._audience = audience
        self._jwk_service = jwk_service

    def generate_token(
        self,
        capture_id: str,
        publisher_id: str,
        device_id: str,
        method: AttestationMethod,
        app_id: str | None = None,
        device_public_key_fingerprint: str | None = None,
    ) -> str:
        """
        Generate a signed JWT trust token.

        Args:
            capture_id: The capture session ID.
            publisher_id: The publisher ID.
            device_id: The device ID.
            method: The attestation method used (sandbox, app_check, app_attest).
            app_id: The app ID from attestation (e.g., bundle ID), if available.
            device_public_key_fingerprint: SHA-256 hex of the device's content-signing
                public key, for cross-layer binding with the media integrity proof.

        Returns the signed JWT string with kid in header for JWKS lookup.
        """
        now = int(datetime.now(UTC).timestamp())

        # Build attestation object
        attestation: dict[str, str] = {"method": method}
        if app_id is not None:
            attestation["app_id"] = app_id

        payload: dict[str, Any] = {
            "iss": self._issuer,
            "aud": self._audience,
            "sub": "capture-service",
            "iat": now,
            "capture_id": capture_id,
            "publisher_id": publisher_id,
            "device_id": device_id,
            "attestation": attestation,
        }

        if device_public_key_fingerprint is not None:
            payload["device_public_key_fingerprint"] = device_public_key_fingerprint

        return jwt.encode(
            payload,
            self._private_key,
            algorithm="ES256",
            headers={"kid": self._jwk_service.get_kid()},
        )


def get_trust_service() -> TrustService:
    """Get the trust service instance."""
    return TrustService(
        private_key=settings.jwt_private_key,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        jwk_service=get_jwk_service_singleton(),
    )
