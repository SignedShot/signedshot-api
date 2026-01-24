from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Publisher
from app.repositories.publisher import PublisherRepository, publisher_repository


class PublisherService:
    """Service for publisher management."""

    def __init__(self, repository: PublisherRepository) -> None:
        self._repository = repository

    async def create(
        self,
        session: AsyncSession,
        name: str,
        firebase_project_id: str | None = None,
        track_devices: bool = False,
    ) -> Publisher:
        """
        Create a new publisher.

        Raises EntityAlreadyExistsError if name or firebase_project_id is already registered.
        """
        return await self._repository.create(
            session,
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
        )


publisher_service = PublisherService(repository=publisher_repository)
