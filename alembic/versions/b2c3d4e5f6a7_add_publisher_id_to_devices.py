"""Add publisher_id to devices

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-23 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add publisher_id column to devices
    op.add_column(
        "devices",
        sa.Column("publisher_id", sa.Uuid(), nullable=False),
    )
    op.create_foreign_key(
        "fk_devices_publisher_id",
        "devices",
        "publishers",
        ["publisher_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_devices_publisher_id"), "devices", ["publisher_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_devices_publisher_id"), table_name="devices")
    op.drop_constraint("fk_devices_publisher_id", "devices", type_="foreignkey")
    op.drop_column("devices", "publisher_id")
