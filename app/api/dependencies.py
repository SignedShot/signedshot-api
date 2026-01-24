import hashlib

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.db.models import Device
from app.exceptions import InvalidCredentialsError
from app.repositories.device import device_repository

security = HTTPBearer()


def _hash_token(token: str) -> str:
    """Hash a token for comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Device:
    """
    Dependency that validates device token and returns the device.

    Raises InvalidCredentialsError if token is invalid or device not found.
    """
    token = credentials.credentials
    token_hash = _hash_token(token)

    device = await device_repository.get_by_token_hash(session, token_hash)
    if device is None:
        raise InvalidCredentialsError("Invalid device token")

    return device
