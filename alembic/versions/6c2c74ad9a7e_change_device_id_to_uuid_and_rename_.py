"""Change device id to UUID and rename device_id to external_id

Revision ID: 6c2c74ad9a7e
Revises: 763a02af6978
Create Date: 2026-01-22 08:09:13.296725

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6c2c74ad9a7e'
down_revision: str | Sequence[str] | None = '763a02af6978'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old table and recreate with new schema
    # This is a breaking change - existing data will be lost
    op.drop_index(op.f('ix_devices_device_id'), table_name='devices')
    op.drop_table('devices')

    op.create_table(
        'devices',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_devices_external_id'), 'devices', ['external_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_devices_external_id'), table_name='devices')
    op.drop_table('devices')

    op.create_table(
        'devices',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_devices_device_id'), 'devices', ['device_id'], unique=True)
