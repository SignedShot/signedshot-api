import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.db.models import Publisher
from app.exceptions import AppCheckError
from app.services.firebase import FirebaseAppCheckError, FirebaseAppCheckService

logger = logging.getLogger(__name__)


@dataclass
class AttestationResult:
    method: str | None  # "app_check", "app_attest", or None
    attested_at: datetime | None
    app_id: str | None


def resolve_attestation(
    token: str | None,
    firebase_service: FirebaseAppCheckService,
    publisher: Publisher,
    is_production: bool,
) -> AttestationResult:
    if token is None:
        if is_production:
            raise AppCheckError("App Check token required in production environment")
        if not publisher.sandbox:
            raise AppCheckError("App Check token required for non-sandbox publishers")

        logger.debug(f"Device registration in sandbox mode, publisher={publisher.id}")
        return AttestationResult(method=None, attested_at=None, app_id=None)

    if not firebase_service.is_initialized:
        logger.error("Firebase App Check token provided but Firebase not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase App Check service not configured",
        )

    try:
        claims = firebase_service.verify_token(token)
        attestation = AttestationResult(
            method="app_check",
            attested_at=datetime.now(UTC),
            app_id=claims.get("app_id"),
        )
        logger.info(
            f"Device registration with App Check verified, "
            f"publisher={publisher.id}, app_id={attestation.app_id}"
        )
        return attestation
    except FirebaseAppCheckError as e:
        raise AppCheckError(str(e)) from e
