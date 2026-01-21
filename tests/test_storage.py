import asyncio

import pytest

from app.storage.memory import MemoryStorage


@pytest.fixture
def storage() -> MemoryStorage:
    """Create a fresh memory storage instance."""
    return MemoryStorage()


async def test_set_and_get(storage: MemoryStorage) -> None:
    """Set a value and retrieve it."""
    await storage.set("key1", "value1")

    result = await storage.get("key1")

    assert result == "value1"


async def test_get_nonexistent_key(storage: MemoryStorage) -> None:
    """Get returns None for nonexistent key."""
    result = await storage.get("nonexistent")

    assert result is None


async def test_delete_existing_key(storage: MemoryStorage) -> None:
    """Delete returns True for existing key."""
    await storage.set("key1", "value1")

    result = await storage.delete("key1")

    assert result is True
    assert await storage.get("key1") is None


async def test_delete_nonexistent_key(storage: MemoryStorage) -> None:
    """Delete returns False for nonexistent key."""
    result = await storage.delete("nonexistent")

    assert result is False


async def test_exists_true(storage: MemoryStorage) -> None:
    """Exists returns True for existing key."""
    await storage.set("key1", "value1")

    result = await storage.exists("key1")

    assert result is True


async def test_exists_false(storage: MemoryStorage) -> None:
    """Exists returns False for nonexistent key."""
    result = await storage.exists("nonexistent")

    assert result is False


async def test_ttl_expires(storage: MemoryStorage) -> None:
    """Value expires after TTL."""
    await storage.set("key1", "value1", ttl_seconds=1)

    # Value should exist immediately
    assert await storage.get("key1") == "value1"

    # Wait for expiry
    await asyncio.sleep(1.1)

    # Value should be gone
    assert await storage.get("key1") is None


async def test_ttl_not_expired(storage: MemoryStorage) -> None:
    """Value exists before TTL expires."""
    await storage.set("key1", "value1", ttl_seconds=10)

    result = await storage.get("key1")

    assert result == "value1"


async def test_overwrite_value(storage: MemoryStorage) -> None:
    """Setting same key overwrites value."""
    await storage.set("key1", "value1")
    await storage.set("key1", "value2")

    result = await storage.get("key1")

    assert result == "value2"


async def test_exists_expired_key(storage: MemoryStorage) -> None:
    """Exists returns False for expired key."""
    await storage.set("key1", "value1", ttl_seconds=1)

    await asyncio.sleep(1.1)

    result = await storage.exists("key1")

    assert result is False
