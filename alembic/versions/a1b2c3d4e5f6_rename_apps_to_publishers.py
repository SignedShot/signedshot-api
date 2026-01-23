"""Rename apps to publishers

Revision ID: a1b2c3d4e5f6
Revises: 97a86f7166f9
Create Date: 2026-01-23 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "97a86f7166f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop foreign key and index on captures.app_id
    op.drop_index(op.f("ix_captures_app_id"), table_name="captures")
    op.drop_constraint("fk_captures_app_id", "captures", type_="foreignkey")

    # Rename app_id column to publisher_id
    op.alter_column("captures", "app_id", new_column_name="publisher_id")

    # Rename apps table to publishers
    op.rename_table("apps", "publishers")

    # Rename index on firebase_project_id
    op.drop_index(op.f("ix_apps_firebase_project_id"), table_name="publishers")
    op.create_index(
        op.f("ix_publishers_firebase_project_id"),
        "publishers",
        ["firebase_project_id"],
        unique=True,
    )

    # Recreate foreign key and index with new names
    op.create_foreign_key(
        "fk_captures_publisher_id",
        "captures",
        "publishers",
        ["publisher_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_captures_publisher_id"), "captures", ["publisher_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key and index on captures.publisher_id
    op.drop_index(op.f("ix_captures_publisher_id"), table_name="captures")
    op.drop_constraint("fk_captures_publisher_id", "captures", type_="foreignkey")

    # Rename index on firebase_project_id back
    op.drop_index(op.f("ix_publishers_firebase_project_id"), table_name="publishers")
    op.create_index(
        op.f("ix_apps_firebase_project_id"),
        "publishers",
        ["firebase_project_id"],
        unique=True,
    )

    # Rename publishers table back to apps
    op.rename_table("publishers", "apps")

    # Rename publisher_id column back to app_id
    op.alter_column("captures", "publisher_id", new_column_name="app_id")

    # Recreate foreign key and index with old names
    op.create_foreign_key(
        "fk_captures_app_id",
        "captures",
        "apps",
        ["app_id"],
        ["id"],
    )
    op.create_index(op.f("ix_captures_app_id"), "captures", ["app_id"], unique=False)
