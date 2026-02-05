"""Add attested_app_id to devices.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2024-01-28 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add attested_app_id column to devices table."""
    op.add_column(
        "devices",
        sa.Column("attested_app_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Remove attested_app_id column from devices table."""
    op.drop_column("devices", "attested_app_id")
