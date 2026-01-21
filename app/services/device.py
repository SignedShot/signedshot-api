import hashlib
import secrets

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

    async def register(
        self, session: AsyncSession, device_id: str
    ) -> tuple[Device, str]:
        """
        Register a new device.

        Returns the device and the plain token (only returned once).
        Raises DeviceAlreadyExistsError if device_id is already registered.
        """
        existing = await self._repository.get_by_device_id(session, device_id)
        if existing:
            raise DeviceAlreadyExistsError(f"Device {device_id} already registered")

        token = self._generate_token()
        token_hash = self._hash_token(token)

        device = await self._repository.create(session, device_id, token_hash)
        return device, token


device_service = DeviceService(repository=device_repository)
