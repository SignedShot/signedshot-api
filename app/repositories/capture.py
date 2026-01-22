import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session
from app.db.models import Capture


class CaptureRepository:
    """Repository for capture data access."""

    async def create(self, session: AsyncSession, device_id: str) -> Capture:
        """Create a new capture record."""
        capture = Capture(device_id=device_id)
        session.add(capture)
        await session.commit()
        await session.refresh(capture)
        return capture

    async def get_by_id(
        self, session: AsyncSession, capture_id: uuid.UUID
    ) -> Capture | None:
        """Get a capture by its ID."""
        result = await session.execute(select(Capture).where(Capture.id == capture_id))
        return result.scalar_one_or_none()

    async def mark_completed(
        self, session: AsyncSession, capture_id: uuid.UUID
    ) -> bool:
        """Mark a capture as completed. Returns True if capture existed."""
        capture = await self.get_by_id(session, capture_id)
        if capture is None:
            return False
        capture.completed_at = datetime.now(UTC)
        await session.commit()
        return True


capture_repository = CaptureRepository()


async def mark_capture_completed(capture_id: str) -> None:
    """Background task to mark a capture as completed."""
    async with async_session() as db:
        await capture_repository.mark_completed(db, uuid.UUID(capture_id))
