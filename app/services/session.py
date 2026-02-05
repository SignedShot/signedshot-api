import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.capture import capture_repository
from app.settings import settings
from app.storage import Storage, get_storage


@dataclass
class SessionData:
    """Data stored in a session."""

    capture_id: str
    publisher_id: str
    device_id: str
    attestation_method: str | None  # None means no attestation (sandbox)


@dataclass
class CreateSessionResult:
    """Result of creating a capture session."""

    capture_id: str
    nonce: str
    expires_at: datetime


class SessionService:
    """Service for managing capture sessions."""

    def __init__(self, storage: Storage, expiry_seconds: int) -> None:
        self._storage = storage
        self._expiry_seconds = expiry_seconds

    def _generate_nonce(self) -> str:
        """Generate a secure random nonce."""
        return secrets.token_urlsafe(32)

    def _session_key(self, nonce: str) -> str:
        """Get the storage key for a session."""
        return f"session:{nonce}"

    async def create(
        self,
        db: AsyncSession,
        publisher_id: uuid.UUID,
        device_id: uuid.UUID,
        attestation_method: str | None,
    ) -> CreateSessionResult:
        """
        Create a new capture session for a device.

        Creates a Capture record in the database and stores session data in cache.

        Args:
            db: Database session.
            publisher_id: Publisher UUID.
            device_id: Device UUID.
            attestation_method: The device's attestation method (e.g., "app_check")
                or None if not attested.
        """
        # Create capture record in database
        capture = await capture_repository.create(db, publisher_id, device_id)
        capture_id = str(capture.id)

        # Generate nonce and expiry
        nonce = self._generate_nonce()
        expires_at = datetime.now(UTC) + timedelta(seconds=self._expiry_seconds)

        # Store session data as JSON
        session_data = json.dumps(
            {
                "capture_id": capture_id,
                "publisher_id": str(publisher_id),
                "device_id": str(device_id),
                "attestation_method": attestation_method,
            }
        )
        await self._storage.set(
            self._session_key(nonce),
            session_data,
            ttl_seconds=self._expiry_seconds,
        )

        return CreateSessionResult(
            capture_id=capture_id,
            nonce=nonce,
            expires_at=expires_at,
        )

    async def get_session_data(self, nonce: str) -> SessionData | None:
        """
        Get the session data for a nonce.

        Returns None if session doesn't exist or is expired.
        """
        value = await self._storage.get(self._session_key(nonce))
        if value is None:
            return None
        data = json.loads(value)
        return SessionData(
            capture_id=data["capture_id"],
            publisher_id=data["publisher_id"],
            device_id=data["device_id"],
            attestation_method=data.get("attestation_method"),
        )

    async def consume(self, nonce: str) -> SessionData | None:
        """
        Consume a session (one-time use).

        Returns the session data if valid, None otherwise.
        Deletes the session after retrieval.
        """
        session_data = await self.get_session_data(nonce)
        if session_data is not None:
            await self._storage.delete(self._session_key(nonce))
        return session_data


def get_session_service() -> SessionService:
    """Get the session service instance."""
    return SessionService(
        storage=get_storage(),
        expiry_seconds=settings.session_expiry_seconds,
    )
