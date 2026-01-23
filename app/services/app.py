from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import App
from app.repositories.app import AppRepository, app_repository


class AppAlreadyExistsError(Exception):
    """Raised when trying to register an app that already exists."""

    pass


class AppService:
    """Service for app registration."""

    def __init__(self, repository: AppRepository) -> None:
        self._repository = repository

    async def register(
        self,
        session: AsyncSession,
        name: str,
        firebase_project_id: str | None = None,
        track_devices: bool = False,
    ) -> App:
        """
        Register a new app.

        Raises AppAlreadyExistsError if name or firebase_project_id is already registered.
        """
        # Check for duplicate name
        existing = await self._repository.get_by_name(session, name)
        if existing:
            raise AppAlreadyExistsError(f"App with name '{name}' already registered")

        # Check for duplicate firebase_project_id if provided
        if firebase_project_id:
            existing = await self._repository.get_by_firebase_project_id(
                session, firebase_project_id
            )
            if existing:
                raise AppAlreadyExistsError(
                    f"App with Firebase project '{firebase_project_id}' already registered"
                )

        return await self._repository.create(
            session,
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
        )


app_service = AppService(repository=app_repository)
