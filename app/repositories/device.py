import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device
from app.exceptions import EntityAlreadyExistsError


class DeviceRepository:
    """Repository for device data access."""

    async def get_by_external_id(
        self, session: AsyncSession, external_id: str
    ) -> Device | None:
        """Get a device by its external_id."""
        result = await session.execute(
            select(Device).where(Device.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token_hash(
        self, session: AsyncSession, token_hash: str
    ) -> Device | None:
        """Get a device by its token hash."""
        result = await session.execute(
            select(Device).where(Device.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        publisher_id: uuid.UUID,
        external_id: str,
        token_hash: str,
        public_key: str,
        device_public_key_fingerprint: str,
        attestation_method: str | None = None,
        attested_at: datetime | None = None,
        attested_app_id: str | None = None,
    ) -> Device:
        """Create a new device.

        Args:
            session: Database session.
            publisher_id: Publisher UUID.
            external_id: External device identifier.
            token_hash: Hashed device token.
            public_key: Base64-encoded content-signing public key.
            device_public_key_fingerprint: SHA-256 hex of the public key.
            attestation_method: Optional attestation method (e.g., "app_check").
            attested_at: Optional timestamp when attestation was verified.
            attested_app_id: Optional app ID from attestation (e.g., bundle ID).

        Raises:
            EntityAlreadyExistsError: If a device with the same external_id
                already exists for this publisher.
        """
        device = Device(
            publisher_id=publisher_id,
            external_id=external_id,
            token_hash=token_hash,
            attestation_method=attestation_method,
            attested_at=attested_at,
            attested_app_id=attested_app_id,
            public_key=public_key,
            device_public_key_fingerprint=device_public_key_fingerprint,
        )
        session.add(device)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise EntityAlreadyExistsError("Device", external_id) from None
        await session.refresh(device)
        return device


device_repository = DeviceRepository()
