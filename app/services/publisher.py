from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Publisher
from app.repositories.publisher import PublisherRepository, publisher_repository


class PublisherAlreadyExistsError(Exception):
    """Raised when trying to create a publisher that already exists."""

    pass


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

        Raises PublisherAlreadyExistsError if name or firebase_project_id is already registered.
        """
        # Check for duplicate name
        existing = await self._repository.get_by_name(session, name)
        if existing:
            raise PublisherAlreadyExistsError(
                f"Publisher with name '{name}' already exists"
            )

        # Check for duplicate firebase_project_id if provided
        if firebase_project_id:
            existing = await self._repository.get_by_firebase_project_id(
                session, firebase_project_id
            )
            if existing:
                raise PublisherAlreadyExistsError(
                    f"Publisher with Firebase project '{firebase_project_id}' already exists"
                )

        return await self._repository.create(
            session,
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
        )


publisher_service = PublisherService(repository=publisher_repository)
