from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageType(str, Enum):
    """Storage backend type."""

    MEMORY = "memory"
    REDIS = "redis"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    app_name: str = "SignedShot API"
    version: str = "0.1.0"
    app_version: str = "dev"  # Set via APP_VERSION env var during deployment
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://localhost/signedshot"

    # Storage
    storage_type: StorageType = StorageType.MEMORY
    redis_url: str = "redis://localhost:6379"

    # Session
    session_expiry_seconds: int = 300  # 5 minutes

    # JWT
    jwt_private_key: str = ""  # ES256 private key in PEM format
    jwt_issuer: str = "signedshot"
    jwt_audience: str = "signedshot"


settings = Settings()
