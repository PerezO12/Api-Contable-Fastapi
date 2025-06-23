"""Update payment schedule percentage precision to support 6 decimal places

Revision ID: update_payment_percentage_precision
Revises: # Será actualizado automáticamente por alembic
Create Date: 2025-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '219968f9f601'  # Última migración
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Actualiza la precisión de la columna percentage en payment_schedules
    de Numeric(5,2) a Numeric(11,6) para soportar hasta 6 decimales
    """
    # Actualizar la columna percentage en payment_schedules
    op.alter_column(
        'payment_schedules',
        'percentage',
        existing_type=sa.Numeric(precision=5, scale=2),
        type_=sa.Numeric(precision=11, scale=6),
        nullable=False,
        comment='Porcentaje a pagar (hasta 6 decimales para mayor precisión)'
    )


def downgrade() -> None:
    """
    Revierte los cambios - vuelve a Numeric(5,2)
    ADVERTENCIA: Esto puede causar pérdida de precisión en los datos
    """
    op.alter_column(
        'payment_schedules',
        'percentage',
        existing_type=sa.Numeric(precision=11, scale=6),
        type_=sa.Numeric(precision=5, scale=2),
        nullable=False,
        comment='Porcentaje a pagar'
    )
