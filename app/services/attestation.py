import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.db.models import AttestationProvider, Publisher
from app.exceptions import AppCheckError
from app.services.firebase import FirebaseAppCheckError, FirebaseAppCheckService

logger = logging.getLogger(__name__)


class InvalidPublisherConfigError(Exception):
    """Raised when publisher has invalid attestation configuration."""

    pass


@dataclass
class AttestationResult:
    method: str | None  # "app_check", "app_attest", or None
    attested_at: datetime | None
    app_id: str | None


def resolve_attestation(
    token: str | None,
    firebase_service: FirebaseAppCheckService,
    publisher: Publisher,
) -> AttestationResult:
    if token is None:
        if publisher.sandbox:
            logger.debug(
                f"Device registration in sandbox mode, publisher={publisher.id}"
            )
            return AttestationResult(method=None, attested_at=None, app_id=None)
        else:
            logger.error(
                f"Attestation token required for non-sandbox publisher, publisher={publisher.id}"
            )
            raise AppCheckError("Attestation token required for non-sandbox publishers")

    if publisher.sandbox and publisher.attestation_provider is AttestationProvider.NONE:
        logger.warning(
            f"Token provided but no provider configured, publisher={publisher.id}"
        )
        raise AppCheckError("Attestation token provided but no attestation_provider")

    if (
        not publisher.sandbox
        and publisher.attestation_provider is AttestationProvider.NONE
    ):
        logger.error(
            f"Invalid publisher config: sandbox=False but no attestation_provider, publisher={publisher.id}"
        )
        raise InvalidPublisherConfigError(
            "Non-sandbox publisher must have an attestation_provider"
        )

    if not firebase_service.is_initialized:
        logger.error("Firebase App Check token provided but Firebase not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase App Check service not configured",
        )

    try:
        claims = firebase_service.verify_token(token)
        app_id = publisher.attestation_bundle_id or claims.get("app_id")
        attestation = AttestationResult(
            method="app_check",
            attested_at=datetime.now(UTC),
            app_id=app_id,
        )
        logger.info(
            f"Device registration with App Check verified, "
            f"publisher={publisher.id}, app_id={attestation.app_id}"
        )
        return attestation
    except FirebaseAppCheckError as e:
        raise AppCheckError(str(e)) from e
