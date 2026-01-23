from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Publisher


class PublisherRepository:
    """Repository for publisher data access."""

    async def get_by_id(
        self, session: AsyncSession, publisher_id: str
    ) -> Publisher | None:
        """Get a publisher by its ID."""
        result = await session.execute(
            select(Publisher).where(Publisher.id == publisher_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, session: AsyncSession, name: str) -> Publisher | None:
        """Get a publisher by its name."""
        result = await session.execute(select(Publisher).where(Publisher.name == name))
        return result.scalar_one_or_none()

    async def get_by_firebase_project_id(
        self, session: AsyncSession, firebase_project_id: str
    ) -> Publisher | None:
        """Get a publisher by its Firebase project ID."""
        result = await session.execute(
            select(Publisher).where(
                Publisher.firebase_project_id == firebase_project_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        name: str,
        firebase_project_id: str | None = None,
        track_devices: bool = False,
    ) -> Publisher:
        """Create a new publisher."""
        publisher = Publisher(
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
            sandbox=True,  # All new publishers start in sandbox mode
        )
        session.add(publisher)
        await session.commit()
        await session.refresh(publisher)
        return publisher


publisher_repository = PublisherRepository()
