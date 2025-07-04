"""update payment schedule percentage precision to 6 decimals

Revision ID: ab3fcba43b29
Revises: 2ae2d2141f9e
Create Date: 2025-06-23 15:58:45.970399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab3fcba43b29'
down_revision: Union[str, None] = '2ae2d2141f9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('payment_schedules', 'percentage',
               existing_type=sa.NUMERIC(precision=5, scale=2),
               type_=sa.Numeric(precision=11, scale=6),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('payment_schedules', 'percentage',
               existing_type=sa.Numeric(precision=11, scale=6),
               type_=sa.NUMERIC(precision=5, scale=2),
               existing_nullable=False)
    # ### end Alembic commands ###