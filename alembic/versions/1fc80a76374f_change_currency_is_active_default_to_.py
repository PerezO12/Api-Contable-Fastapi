"""Change currency is_active default to false

Revision ID: 1fc80a76374f
Revises: f1cc3272d3ac
Create Date: 2025-07-06 22:13:28.745642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fc80a76374f'
down_revision: Union[str, None] = 'f1cc3272d3ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change default value for is_active in currencies table to False."""
    # Change default value for is_active in currencies table to False
    op.alter_column('currencies', 'is_active',
                   existing_type=sa.BOOLEAN(),
                   server_default=sa.text('false'),
                   existing_nullable=False)


def downgrade() -> None:
    """Restore default value for is_active in currencies table to True."""
    # Restore default value for is_active in currencies table to True
    op.alter_column('currencies', 'is_active',
                   existing_type=sa.BOOLEAN(),
                   server_default=sa.text('true'),
                   existing_nullable=False)