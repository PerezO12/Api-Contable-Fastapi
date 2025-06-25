"""add_allows_reconciliation_to_accounts

Revision ID: a9fb41079bc7
Revises: 622f005debcd
Create Date: 2025-06-24 23:51:51.149129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9fb41079bc7'
down_revision: Union[str, None] = '622f005debcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add allows_reconciliation column to accounts table
    op.add_column('accounts', sa.Column('allows_reconciliation', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove allows_reconciliation column from accounts table
    op.drop_column('accounts', 'allows_reconciliation')