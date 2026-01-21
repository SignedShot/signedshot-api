"""Session storage module."""

from app.storage.base import Storage
from app.storage.memory import MemoryStorage

# Singleton instance for the application
_storage: Storage | None = None


def get_storage() -> Storage:
    """Get the storage instance."""
    global _storage
    if _storage is None:
        _storage = MemoryStorage()
    return _storage


__all__ = ["Storage", "MemoryStorage", "get_storage"]
