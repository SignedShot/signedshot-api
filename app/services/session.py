import secrets
from datetime import UTC, datetime, timedelta

from app.settings import settings
from app.storage import Storage, get_storage


class SessionService:
    """Service for managing capture sessions."""

    def __init__(self, storage: Storage, expiry_seconds: int) -> None:
        self._storage = storage
        self._expiry_seconds = expiry_seconds

    def _generate_session_id(self) -> str:
        """Generate a secure random session ID."""
        return secrets.token_urlsafe(32)

    def _session_key(self, session_id: str) -> str:
        """Get the storage key for a session."""
        return f"session:{session_id}"

    async def create(self, device_id: str) -> tuple[str, datetime]:
        """
        Create a new capture session for a device.

        Returns the session_id and expiry time.
        """
        session_id = self._generate_session_id()
        expires_at = datetime.now(UTC) + timedelta(seconds=self._expiry_seconds)

        # Store device_id as the session value
        await self._storage.set(
            self._session_key(session_id),
            device_id,
            ttl_seconds=self._expiry_seconds,
        )

        return session_id, expires_at

    async def get_device_id(self, session_id: str) -> str | None:
        """
        Get the device_id for a session.

        Returns None if session doesn't exist or is expired.
        """
        return await self._storage.get(self._session_key(session_id))

    async def consume(self, session_id: str) -> str | None:
        """
        Consume a session (one-time use).

        Returns the device_id if valid, None otherwise.
        Deletes the session after retrieval.
        """
        device_id = await self.get_device_id(session_id)
        if device_id is not None:
            await self._storage.delete(self._session_key(session_id))
        return device_id


def get_session_service() -> SessionService:
    """Get the session service instance."""
    return SessionService(
        storage=get_storage(),
        expiry_seconds=settings.session_expiry_seconds,
    )
