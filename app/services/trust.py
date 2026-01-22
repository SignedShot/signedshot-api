from datetime import UTC, datetime

import jwt

from app.settings import settings


class TrustService:
    """Service for generating trust tokens."""

    def __init__(self, private_key: str, issuer: str, audience: str) -> None:
        self._private_key = private_key
        self._issuer = issuer
        self._audience = audience

    def generate_token(self, capture_id: str, device_id: str) -> str:
        """
        Generate a signed JWT trust token.

        Returns the signed JWT string.
        """
        now = int(datetime.now(UTC).timestamp())

        payload = {
            "iss": self._issuer,
            "aud": self._audience,
            "sub": "capture-service",
            "iat": now,
            "capture_id": capture_id,
            "device_id": device_id,
        }

        return jwt.encode(payload, self._private_key, algorithm="ES256")


def get_trust_service() -> TrustService:
    """Get the trust service instance."""
    return TrustService(
        private_key=settings.jwt_private_key,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
