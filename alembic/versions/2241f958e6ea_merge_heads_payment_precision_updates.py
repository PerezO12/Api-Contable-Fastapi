"""merge heads - payment precision updates

Revision ID: 2241f958e6ea
Revises: ab3fcba43b29, f1a2b3c4d5e6
Create Date: 2025-06-24 00:26:44.103469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2241f958e6ea'
down_revision: Union[str, None] = ('ab3fcba43b29', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass