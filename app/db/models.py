import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Publisher(Base):
    """Registered publisher model."""

    __tablename__ = "publishers"
    __table_args__ = (
        # Case-insensitive unique index on name (created via migration)
        Index("ix_publishers_name_lower", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    firebase_project_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    track_devices: Mapped[bool] = mapped_column(Boolean, default=False)
    sandbox: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Device(Base):
    """Registered device model."""

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint(
            "publisher_id", "external_id", name="uq_device_publisher_external"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("publishers.id"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Capture(Base):
    """Capture session record for audit trail."""

    __tablename__ = "captures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    publisher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("publishers.id"), index=True
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("devices.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
