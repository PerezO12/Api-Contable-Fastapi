"""add IMPUESTOS to account category

Revision ID: 6a705b047320
Revises: 871486a82c1d
Create Date: 2025-06-26 12:09:54.943298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a705b047320'
down_revision: Union[str, None] = '871486a82c1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar el valor 'IMPUESTOS' al enum accountcategory
    op.execute("ALTER TYPE accountcategory ADD VALUE 'IMPUESTOS'")


def downgrade() -> None:
    """Downgrade schema."""
    # No podemos eliminar valores de un enum en PostgreSQL
    # La única opción sería crear un nuevo tipo sin ese valor
    # y migrar todas las tablas, lo cual es riesgoso
    pass