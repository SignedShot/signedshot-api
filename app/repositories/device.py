from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device


class DeviceRepository:
    """Repository for device data access."""

    async def get_by_device_id(
        self, session: AsyncSession, device_id: str
    ) -> Device | None:
        """Get a device by its device_id."""
        result = await session.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, session: AsyncSession, device_id: str, token_hash: str
    ) -> Device:
        """Create a new device."""
        device = Device(device_id=device_id, token_hash=token_hash)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device


device_repository = DeviceRepository()
