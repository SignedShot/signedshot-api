import uuid

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
    ) -> Device:
        """Create a new device.

        Raises:
            EntityAlreadyExistsError: If a device with the same external_id
                already exists for this publisher.
        """
        device = Device(
            publisher_id=publisher_id,
            external_id=external_id,
            token_hash=token_hash,
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
