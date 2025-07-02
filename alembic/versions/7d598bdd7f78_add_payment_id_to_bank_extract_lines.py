"""add_payment_id_to_bank_extract_lines

Revision ID: 7d598bdd7f78
Revises: 6a705b047320
Create Date: 2025-07-01 16:58:27.633492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d598bdd7f78'
down_revision: Union[str, None] = '6a705b047320'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add payment_id column to bank_extract_lines table
    op.add_column('bank_extract_lines', sa.Column('payment_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_bank_extract_lines_payment_id',
        'bank_extract_lines', 
        'payments',
        ['payment_id'], 
        ['id']
    )
    
    # Add index for better performance
    op.create_index(
        'ix_bank_extract_lines_payment_id',
        'bank_extract_lines',
        ['payment_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('ix_bank_extract_lines_payment_id', 'bank_extract_lines')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_bank_extract_lines_payment_id', 'bank_extract_lines', type_='foreignkey')
    
    # Drop column
    op.drop_column('bank_extract_lines', 'payment_id')