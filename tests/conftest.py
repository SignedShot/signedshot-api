import os

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

# Generate a test ES256 private key for unit tests
_test_private_key = ec.generate_private_key(ec.SECP256R1())
_test_private_key_pem = _test_private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")

# Ensure tests use memory storage and have a test JWT key
os.environ["STORAGE_TYPE"] = "memory"
os.environ["JWT_PRIVATE_KEY"] = _test_private_key_pem

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singletons before each test."""
    import app.services.jwk as jwk_module
    import app.storage as storage_module

    storage_module._storage = None
    jwk_module._jwk_service = None


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def test_private_key_pem() -> str:
    """Get the test private key PEM."""
    return _test_private_key_pem
