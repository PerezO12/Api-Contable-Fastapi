"""add payment to journaletrytpype

Revision ID: 63f5f0bff4c9
Revises: 7d598bdd7f78
Create Date: 2025-07-01 21:08:47.810952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63f5f0bff4c9'
down_revision: Union[str, None] = '7d598bdd7f78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass