"""Integration test fixtures using testcontainers."""

import asyncio
import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a Postgres container for integration tests."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    """Start a Redis container for integration tests."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    """Get the async database URL from the container."""
    # testcontainers returns psycopg2 URL, we need asyncpg
    url = postgres_container.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def sync_database_url(postgres_container: PostgresContainer) -> str:
    """Get the sync database URL from the container."""
    url = postgres_container.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql://")


@pytest.fixture(scope="session")
def redis_url(redis_container: RedisContainer) -> str:
    """Get the Redis URL from the container."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


@pytest.fixture(scope="session")
def test_private_key() -> str:
    """Generate a test ES256 private key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


@pytest.fixture(scope="session")
def _setup_env(
    database_url: str,
    redis_url: str,
    test_private_key: str,
) -> Generator[None, None, None]:
    """Set up environment variables for tests (session-scoped)."""
    # Set environment variables before importing app modules
    os.environ["DATABASE_URL"] = database_url
    os.environ["STORAGE_TYPE"] = "redis"
    os.environ["REDIS_URL"] = redis_url
    os.environ["JWT_PRIVATE_KEY"] = test_private_key
    os.environ["JWT_ISSUER"] = "https://dev-api.signedshot.io"
    os.environ["DEBUG"] = "true"

    yield


@pytest.fixture(scope="session")
def _setup_db(
    _setup_env: None,  # noqa: ARG001
    sync_database_url: str,
) -> Generator[None, None, None]:
    """Create database tables (session-scoped)."""
    # Remove cached app modules to force reimport with new settings
    modules_to_remove = [key for key in sys.modules if key.startswith("app.")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    from sqlalchemy import create_engine, text

    from app.db.models import Base

    sync_engine = create_engine(sync_database_url)
    Base.metadata.create_all(sync_engine)

    # Create case-insensitive unique index on publisher name
    # (This is normally created via alembic migration)
    with sync_engine.connect() as conn:
        # Drop the regular index created by SQLAlchemy
        conn.execute(text("DROP INDEX IF EXISTS ix_publishers_name_lower"))
        # Create case-insensitive unique index
        conn.execute(
            text(
                "CREATE UNIQUE INDEX ix_publishers_name_lower "
                "ON publishers (LOWER(name))"
            )
        )
        conn.commit()

    sync_engine.dispose()

    yield

    # Cleanup: drop all tables
    sync_engine = create_engine(sync_database_url)
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest.fixture(scope="function")
def integration_client(
    _setup_db: None,  # noqa: ARG001
    sync_database_url: str,
) -> Generator[TestClient, None, None]:
    """Create a test client with real Postgres and Redis backends."""
    # Remove cached app modules to get fresh imports with fresh engine
    modules_to_remove = [key for key in sys.modules if key.startswith("app.")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    from app.main import app

    with TestClient(app) as client:
        yield client

    # Dispose of the async engine to clean up connections
    from app.db.engine import engine

    loop = asyncio.new_event_loop()
    loop.run_until_complete(engine.dispose())
    loop.close()

    # Clean up data between tests using sync connection
    # Order matters due to foreign key constraints
    from sqlalchemy import create_engine, text

    sync_engine = create_engine(sync_database_url)
    with sync_engine.connect() as conn:
        conn.execute(text("DELETE FROM captures"))
        conn.execute(text("DELETE FROM devices"))
        conn.execute(text("DELETE FROM publishers"))
        conn.commit()
    sync_engine.dispose()

    # Reset singletons for next test
    import app.services.jwk
    import app.storage

    app.storage._storage = None
    app.services.jwk._jwk_service = None
