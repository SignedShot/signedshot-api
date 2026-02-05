from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AttestationProvider, Publisher
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
        sandbox: bool = True,
        attestation_provider: AttestationProvider = AttestationProvider.NONE,
        attestation_bundle_id: str | None = None,
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
            sandbox=sandbox,
            attestation_provider=attestation_provider,
            attestation_bundle_id=attestation_bundle_id,
        )

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
        """
        Update a publisher with the provided fields.

        Only non-None fields will be updated.

        Raises EntityAlreadyExistsError if the new values conflict with existing data.
        """
        return await self._repository.update(
            session,
            publisher=publisher,
            name=name,
            firebase_project_id=firebase_project_id,
            track_devices=track_devices,
            sandbox=sandbox,
            attestation_provider=attestation_provider,
            attestation_bundle_id=attestation_bundle_id,
        )


publisher_service = PublisherService(repository=publisher_repository)
