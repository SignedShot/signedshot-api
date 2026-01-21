from typing import Protocol


class Storage(Protocol):
    """Storage interface for key-value operations with optional TTL."""

    async def get(self, key: str) -> str | None:
        """Get a value by key. Returns None if not found or expired."""
        ...

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Set a value with optional TTL in seconds."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        ...
