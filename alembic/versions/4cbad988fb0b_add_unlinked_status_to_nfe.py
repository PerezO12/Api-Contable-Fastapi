"""add_unlinked_status_to_nfe

Revision ID: 4cbad988fb0b
Revises: 0964f13a3192
Create Date: 2025-06-25 15:02:34.749564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cbad988fb0b'
down_revision: Union[str, None] = '0964f13a3192'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar nuevo valor al enum NFeStatus
    connection = op.get_bind()
    connection.execute(sa.text("ALTER TYPE nfestatus ADD VALUE 'UNLINKED'"))


def downgrade() -> None:
    """Downgrade schema."""
    # No es posible quitar un valor de enum en PostgreSQL sin reconstruir el tipo
    # Esta migración no es reversible
    pass