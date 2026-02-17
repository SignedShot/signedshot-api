"""add public_key and device_public_key_fingerprint to devices

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-02-16 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Pre-launch: delete existing devices (they lack a public key and
    # cannot produce valid sidecars with cross-layer binding).
    # Captures reference devices via FK, so delete them first.
    op.execute("DELETE FROM captures")
    op.execute("DELETE FROM devices")

    op.add_column(
        "devices",
        sa.Column("public_key", sa.String(120), nullable=False),
    )
    op.add_column(
        "devices",
        sa.Column("device_public_key_fingerprint", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("devices", "device_public_key_fingerprint")
    op.drop_column("devices", "public_key")
