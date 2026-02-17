import base64
import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device
from app.repositories.device import DeviceRepository, device_repository


class DeviceService:
    """Service for device registration."""

    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def _generate_token(self) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _compute_fingerprint(public_key: str) -> str:
        """Compute SHA-256 fingerprint of a Base64-encoded public key."""
        raw_bytes = base64.b64decode(public_key)
        return hashlib.sha256(raw_bytes).hexdigest()

    async def create(
        self,
        session: AsyncSession,
        publisher_id: uuid.UUID,
        external_id: str,
        public_key: str,
        attestation_method: str | None = None,
        attested_at: datetime | None = None,
        attested_app_id: str | None = None,
    ) -> tuple[Device, str]:
        """
        Create a new device.

        Args:
            session: Database session.
            publisher_id: Publisher UUID.
            external_id: External device identifier.
            public_key: Base64-encoded uncompressed EC public key (65 bytes)
                for cross-layer binding.
            attestation_method: Optional attestation method (e.g., "app_check").
            attested_at: Optional timestamp when attestation was verified.
            attested_app_id: Optional app ID from attestation (e.g., bundle ID).

        Returns the device and the plain token (only returned once).
        Raises EntityAlreadyExistsError if external_id is already registered for this publisher.
        """
        token = self._generate_token()
        token_hash = self._hash_token(token)

        fingerprint = self._compute_fingerprint(public_key)

        device = await self._repository.create(
            session,
            publisher_id,
            external_id,
            token_hash,
            attestation_method=attestation_method,
            attested_at=attested_at,
            attested_app_id=attested_app_id,
            public_key=public_key,
            device_public_key_fingerprint=fingerprint,
        )

        return device, token


device_service = DeviceService(repository=device_repository)
