import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from app.schemas.jwk import JWK, JWKSResponse
from app.settings import settings


class JWKService:
    """Service for managing JSON Web Keys."""

    def __init__(self, private_key_pem: str) -> None:
        self._private_key_pem = private_key_pem
        self._cached_jwk: JWK | None = None
        self._kid: str | None = None

    def _load_private_key(self) -> EllipticCurvePrivateKey:
        """Load the EC private key from PEM."""
        key = load_pem_private_key(self._private_key_pem.encode("utf-8"), password=None)
        if not isinstance(key, EllipticCurvePrivateKey):
            raise ValueError("Private key must be an EC key")
        return key

    @staticmethod
    def _int_to_base64url(value: int, byte_length: int) -> str:
        """Convert an integer to base64url-encoded bytes."""
        value_bytes = value.to_bytes(byte_length, "big")
        return base64.urlsafe_b64encode(value_bytes).decode("ascii").rstrip("=")

    def _create_jwk(self) -> JWK:
        """Create a JWK from the private key."""
        private_key = self._load_private_key()
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()

        # Convert coordinates to base64url (32 bytes each for P-256)
        x = self._int_to_base64url(public_numbers.x, 32)
        y = self._int_to_base64url(public_numbers.y, 32)

        # Generate kid from hash of coordinates
        content = f"{public_numbers.x}:{public_numbers.y}".encode()
        kid = hashlib.sha256(content).hexdigest()

        return JWK(
            kty="EC",
            crv="P-256",
            x=x,
            y=y,
            use="sig",
            alg="ES256",
            kid=kid,
        )

    def get_jwk(self) -> JWK:
        """Get the JWK, creating and caching it if necessary."""
        if self._cached_jwk is None:
            self._cached_jwk = self._create_jwk()
        return self._cached_jwk

    def get_kid(self) -> str:
        """Get the key ID."""
        if self._kid is None:
            self._kid = self.get_jwk().kid
        return self._kid

    def get_jwks(self) -> JWKSResponse:
        """Get the JWKS response with all public keys."""
        return JWKSResponse(keys=[self.get_jwk()])


def get_jwk_service() -> JWKService:
    """Get the JWK service instance."""
    return JWKService(private_key_pem=settings.jwt_private_key)


# Singleton instance for dependency injection
_jwk_service: JWKService | None = None


def get_jwk_service_singleton() -> JWKService:
    """Get or create the singleton JWK service instance."""
    global _jwk_service
    if _jwk_service is None:
        _jwk_service = get_jwk_service()
    return _jwk_service
