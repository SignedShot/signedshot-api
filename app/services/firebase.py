"""Firebase App Check verification service."""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import app_check, credentials

from app.settings import settings

logger = logging.getLogger(__name__)


class FirebaseAppCheckError(Exception):
    """Error during Firebase App Check verification."""

    pass


class FirebaseAppCheckService:
    """Service for verifying Firebase App Check tokens."""

    def __init__(self, project_id: str, credentials_json: str) -> None:
        self._project_id = project_id
        self._credentials_json = credentials_json
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize Firebase Admin SDK.

        Returns True if initialized successfully, False otherwise.
        Should be called once at application startup.
        """
        if self._initialized:
            return True

        if not self._credentials_json:
            logger.info("Firebase credentials not configured, App Check disabled")
            return False

        try:
            # Try parsing as JSON string first
            try:
                creds_dict = json.loads(self._credentials_json)
                cred = credentials.Certificate(creds_dict)
            except json.JSONDecodeError:
                # Treat as file path
                path = Path(self._credentials_json)
                if not path.exists():
                    logger.error(f"Firebase credentials file not found: {path}")
                    return False
                cred = credentials.Certificate(str(path))

            # Initialize Firebase Admin SDK
            firebase_admin.initialize_app(  # type: ignore[reportUnknownMemberType]
                cred,
                options={"projectId": self._project_id},
            )
            self._initialized = True
            logger.info(
                f"Firebase Admin SDK initialized for project: {self._project_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            return False

    def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify a Firebase App Check token.

        Args:
            token: The App Check token from X-Attestation-Token header.

        Returns:
            The decoded token claims.

        Raises:
            FirebaseAppCheckError: If verification fails or Firebase not initialized.
        """
        if not self._initialized:
            raise FirebaseAppCheckError("Firebase not initialized")

        try:
            # Verify the App Check token
            decoded_claims: dict[str, Any] = app_check.verify_token(token)  # type: ignore[reportUnknownMemberType]
            logger.debug(
                f"App Check token verified, app_id: {decoded_claims.get('app_id')}"
            )
            return decoded_claims
        except Exception as e:
            logger.warning(f"App Check token verification failed: {e}")
            raise FirebaseAppCheckError(f"Invalid App Check token: {e}") from e

    @property
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized


@lru_cache
def get_firebase_service() -> FirebaseAppCheckService:
    """Get the Firebase App Check service singleton."""
    service = FirebaseAppCheckService(
        project_id=settings.firebase_project_id,
        credentials_json=settings.firebase_credentials_json,
    )
    service.initialize()
    return service
