from datetime import UTC, datetime
from typing import Literal

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
    ) -> str:
        """
        Generate a signed JWT trust token.

        Args:
            capture_id: The capture session ID.
            publisher_id: The publisher ID.
            device_id: The device ID.
            method: The attestation method used (sandbox, app_check, app_attest).

        Returns the signed JWT string with kid in header for JWKS lookup.
        """
        now = int(datetime.now(UTC).timestamp())

        payload = {
            "iss": self._issuer,
            "aud": self._audience,
            "sub": "capture-service",
            "iat": now,
            "capture_id": capture_id,
            "publisher_id": publisher_id,
            "device_id": device_id,
            "method": method,
        }

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
