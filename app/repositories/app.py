from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import App


class AppRepository:
    """Repository for app data access."""

    async def get_by_id(self, session: AsyncSession, app_id: str) -> App | None:
        """Get an app by its ID."""
        result = await session.execute(select(App).where(App.id == app_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, session: AsyncSession, name: str) -> App | None:
        """Get an app by its name."""
        result = await session.execute(select(App).where(App.name == name))
        return result.scalar_one_or_none()

    async def get_by_firebase_project_id(
        self, session: AsyncSession, firebase_project_id: str
    ) -> App | None:
        """Get an app by its Firebase project ID."""
        result = await session.execute(
            select(App).where(App.firebase_project_id == firebase_project_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        name: str,
        firebase_project_id: str | None = None,
        track_devices: bool = False,
    ) -> App:
        """Create a new app."""
        app = App(
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
            sandbox=True,  # All new apps start in sandbox mode
        )
        session.add(app)
        await session.commit()
        await session.refresh(app)
        return app


app_repository = AppRepository()
