"""Merge device and capture migrations

Revision ID: 0cd9dad03fad
Revises: 6c2c74ad9a7e, 9ce16c51d4f0
Create Date: 2026-01-22 10:16:27.111359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cd9dad03fad'
down_revision: Union[str, Sequence[str], None] = ('6c2c74ad9a7e', '9ce16c51d4f0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
