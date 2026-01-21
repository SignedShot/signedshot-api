"""Session storage module."""
import logging

from redis.asyncio import Redis

from app.settings import StorageType, settings
from app.storage.base import Storage
from app.storage.memory import MemoryStorage
from app.storage.redis import RedisStorage

logger = logging.getLogger(__name__)

# Singleton instance for the application
_storage: Storage | None = None


def get_storage() -> Storage:
    """Get the storage instance based on settings."""
    global _storage
    if _storage is None:
        if settings.storage_type == StorageType.REDIS:
            logger.info("Using Redis storage")
            client = Redis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
            _storage = RedisStorage(client)
        else:
            logger.info("Using Memory storage")
            _storage = MemoryStorage()
    return _storage


__all__ = ["Storage", "MemoryStorage", "RedisStorage", "get_storage"]
