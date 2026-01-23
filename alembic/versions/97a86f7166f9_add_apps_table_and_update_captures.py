"""Add apps table and update captures

Revision ID: 97a86f7166f9
Revises: 9ce16c51d4f0
Create Date: 2026-01-22 12:46:39.942036

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "97a86f7166f9"
down_revision: str | Sequence[str] | None = "9ce16c51d4f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create apps table
    op.create_table(
        "apps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("firebase_project_id", sa.String(length=255), nullable=True),
        sa.Column(
            "track_devices", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("sandbox", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_apps_firebase_project_id"),
        "apps",
        ["firebase_project_id"],
        unique=True,
    )

    # Add app_id to captures (nullable for now to handle existing data)
    op.add_column(
        "captures",
        sa.Column("app_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_captures_app_id",
        "captures",
        "apps",
        ["app_id"],
        ["id"],
    )
    op.create_index(op.f("ix_captures_app_id"), "captures", ["app_id"], unique=False)

    # Make device_id nullable
    op.alter_column(
        "captures",
        "device_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Make device_id non-nullable (will fail if nulls exist)
    op.alter_column(
        "captures",
        "device_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    # Remove app_id from captures
    op.drop_index(op.f("ix_captures_app_id"), table_name="captures")
    op.drop_constraint("fk_captures_app_id", "captures", type_="foreignkey")
    op.drop_column("captures", "app_id")

    # Drop apps table
    op.drop_index(op.f("ix_apps_firebase_project_id"), table_name="apps")
    op.drop_table("apps")
