import time
from dataclasses import dataclass


@dataclass
class _Entry:
    value: str
    expires_at: float | None = None


class MemoryStorage:
    """In-memory storage implementation with TTL support."""

    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}

    def _is_expired(self, entry: _Entry) -> bool:
        if entry.expires_at is None:
            return False
        return time.time() > entry.expires_at

    async def get(self, key: str) -> str | None:
        """Get a value by key. Returns None if not found or expired."""
        entry = self._data.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._data[key]
            return None
        return entry.value

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Set a value with optional TTL in seconds."""
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds
        self._data[key] = _Entry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return await self.get(key) is not None
