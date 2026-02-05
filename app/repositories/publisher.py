from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AttestationProvider, Publisher
from app.exceptions import EntityAlreadyExistsError


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
        sandbox: bool = True,
        attestation_provider: AttestationProvider = AttestationProvider.NONE,
        attestation_bundle_id: str | None = None,
    ) -> Publisher:
        """Create a new publisher.

        Raises:
            EntityAlreadyExistsError: If a publisher with the same name or
                firebase_project_id already exists.
        """
        publisher = Publisher(
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
            sandbox=sandbox,
            attestation_provider=attestation_provider,
            attestation_bundle_id=attestation_bundle_id,
        )
        session.add(publisher)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise EntityAlreadyExistsError("Publisher", name) from None
        await session.refresh(publisher)
        return publisher

    async def update(
        self,
        session: AsyncSession,
        publisher: Publisher,
        name: str | None = None,
        firebase_project_id: str | None = None,
        track_devices: bool | None = None,
        sandbox: bool | None = None,
        attestation_provider: AttestationProvider | None = None,
        attestation_bundle_id: str | None = None,
    ) -> Publisher:
        """Update a publisher with the provided fields.

        Only non-None fields will be updated.

        Raises:
            EntityAlreadyExistsError: If the new name or firebase_project_id
                conflicts with an existing publisher.
        """
        if name is not None:
            publisher.name = name
        if firebase_project_id is not None:
            publisher.firebase_project_id = firebase_project_id
        if track_devices is not None:
            publisher.track_devices = track_devices
        if sandbox is not None:
            publisher.sandbox = sandbox
        if attestation_provider is not None:
            publisher.attestation_provider = attestation_provider
        if attestation_bundle_id is not None:
            publisher.attestation_bundle_id = attestation_bundle_id

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise EntityAlreadyExistsError(
                "Publisher", name or publisher.name
            ) from None
        await session.refresh(publisher)
        return publisher


publisher_repository = PublisherRepository()
