"""Add unique constraints for publisher name and device external_id

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-24 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Case-insensitive unique index on publisher name
    op.execute(
        text(
            "CREATE UNIQUE INDEX ix_publishers_name_lower "
            "ON publishers (LOWER(name))"
        )
    )

    # Remove global unique constraint on external_id
    op.drop_index("ix_devices_external_id", table_name="devices")

    # Add composite unique constraint (publisher_id + external_id)
    op.create_unique_constraint(
        "uq_device_publisher_external",
        "devices",
        ["publisher_id", "external_id"],
    )

    # Keep a non-unique index on external_id for query performance
    op.create_index("ix_devices_external_id", "devices", ["external_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove non-unique index
    op.drop_index("ix_devices_external_id", table_name="devices")

    # Remove composite unique constraint
    op.drop_constraint("uq_device_publisher_external", "devices", type_="unique")

    # Restore global unique index on external_id
    op.create_index(
        "ix_devices_external_id", "devices", ["external_id"], unique=True
    )

    # Drop case-insensitive index on publisher name
    op.drop_index("ix_publishers_name_lower", table_name="publishers")
