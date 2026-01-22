import os

import pytest
from fastapi.testclient import TestClient

# Ensure tests use memory storage
os.environ["STORAGE_TYPE"] = "memory"

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_storage() -> None:
    """Reset the storage singleton before each test to use memory storage."""
    import app.storage as storage_module

    storage_module._storage = None


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)
