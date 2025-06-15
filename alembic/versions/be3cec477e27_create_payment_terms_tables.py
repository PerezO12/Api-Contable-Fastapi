"""create_payment_terms_tables

Revision ID: be3cec477e27
Revises: e947d2ee609f
Create Date: 2025-06-14 22:17:39.970728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be3cec477e27'
down_revision: Union[str, None] = 'e947d2ee609f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create payment_terms table
    op.create_table(
        'payment_terms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_payment_terms_code'), 'payment_terms', ['code'], unique=False)
    
    # Create payment_schedules table
    op.create_table(
        'payment_schedules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('payment_terms_id', sa.UUID(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_terms_id'], ['payment_terms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Now create the foreign key from journal_entry_lines to payment_terms
    op.create_foreign_key(
        op.f('fk_journal_entry_lines_payment_terms_id_payment_terms'), 
        'journal_entry_lines', 
        'payment_terms', 
        ['payment_terms_id'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key from journal_entry_lines first
    op.drop_constraint(
        op.f('fk_journal_entry_lines_payment_terms_id_payment_terms'), 
        'journal_entry_lines', 
        type_='foreignkey'
    )
    
    # Drop payment_schedules table first (due to foreign key)
    op.drop_table('payment_schedules')
    
    # Drop payment_terms table
    op.drop_index(op.f('ix_payment_terms_code'), table_name='payment_terms')
    op.drop_table('payment_terms')