from redis.asyncio import Redis


class RedisStorage:
    """Redis storage implementation with TTL support."""

    def __init__(self, client: Redis) -> None:  # type: ignore[type-arg]
        self._client = client

    async def get(self, key: str) -> str | None:
        """Get a value by key. Returns None if not found or expired."""
        value = await self._client.get(key)
        if value is None:
            return None
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Set a value with optional TTL in seconds."""
        if ttl_seconds is not None:
            await self._client.set(key, value, ex=ttl_seconds)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        result = await self._client.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        result = await self._client.exists(key)
        return result > 0
