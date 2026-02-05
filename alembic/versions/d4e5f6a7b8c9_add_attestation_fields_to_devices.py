"""Add attestation fields to devices.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2024-01-27 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add attestation_method and attested_at columns to devices table."""
    op.add_column(
        "devices",
        sa.Column("attestation_method", sa.String(50), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove attestation columns from devices table."""
    op.drop_column("devices", "attested_at")
    op.drop_column("devices", "attestation_method")
