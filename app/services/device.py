import hashlib
import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device
from app.repositories.device import DeviceRepository, device_repository


class DeviceAlreadyExistsError(Exception):
    """Raised when trying to register a device that already exists."""

    pass


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

    async def create(
        self, session: AsyncSession, publisher_id: uuid.UUID, external_id: str
    ) -> tuple[Device, str]:
        """
        Create a new device.

        Returns the device and the plain token (only returned once).
        Raises DeviceAlreadyExistsError if external_id is already registered.
        """
        existing = await self._repository.get_by_external_id(session, external_id)
        if existing:
            raise DeviceAlreadyExistsError(f"Device {external_id} already registered")

        token = self._generate_token()
        token_hash = self._hash_token(token)

        device = await self._repository.create(
            session, publisher_id, external_id, token_hash
        )
        return device, token


device_service = DeviceService(repository=device_repository)
