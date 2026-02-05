"""add attestation_provider to publishers

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-05 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the enum type
    attestation_provider_enum = sa.Enum(
        "NONE", "FIREBASE_APP_CHECK", name="attestationprovider"
    )
    attestation_provider_enum.create(op.get_bind(), checkfirst=True)

    # Add attestation_provider column with default value
    op.add_column(
        "publishers",
        sa.Column(
            "attestation_provider",
            attestation_provider_enum,
            server_default="NONE",
            nullable=False,
        ),
    )

    # Add attestation_bundle_id column
    op.add_column(
        "publishers",
        sa.Column("attestation_bundle_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("publishers", "attestation_bundle_id")
    op.drop_column("publishers", "attestation_provider")

    # Drop the enum type
    sa.Enum(name="attestationprovider").drop(op.get_bind(), checkfirst=True)
