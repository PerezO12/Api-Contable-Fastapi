"""Add payment account configuration to journals

Revision ID: add_payment_accounts_to_journals
Revises: 
Create Date: 2025-07-05 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_payment_accounts_to_journals'
down_revision = 'a7a33b0d5323'  # This should be set to the latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add payment account configuration fields to journals table"""
    
    # Add new columns for payment account configuration
    op.add_column('journals', sa.Column('customer_receivable_account_id', sa.UUID(), nullable=True))
    op.add_column('journals', sa.Column('supplier_payable_account_id', sa.UUID(), nullable=True))
    op.add_column('journals', sa.Column('cash_difference_account_id', sa.UUID(), nullable=True))
    op.add_column('journals', sa.Column('bank_charges_account_id', sa.UUID(), nullable=True))
    op.add_column('journals', sa.Column('currency_exchange_account_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_journals_customer_receivable_account',
        'journals', 'accounts',
        ['customer_receivable_account_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_journals_supplier_payable_account',
        'journals', 'accounts',
        ['supplier_payable_account_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_journals_cash_difference_account',
        'journals', 'accounts',
        ['cash_difference_account_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_journals_bank_charges_account',
        'journals', 'accounts',
        ['bank_charges_account_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_journals_currency_exchange_account',
        'journals', 'accounts',
        ['currency_exchange_account_id'], ['id']
    )


def downgrade():
    """Remove payment account configuration fields from journals table"""
    
    # Drop foreign key constraints
    op.drop_constraint('fk_journals_currency_exchange_account', 'journals', type_='foreignkey')
    op.drop_constraint('fk_journals_bank_charges_account', 'journals', type_='foreignkey')
    op.drop_constraint('fk_journals_cash_difference_account', 'journals', type_='foreignkey')
    op.drop_constraint('fk_journals_supplier_payable_account', 'journals', type_='foreignkey')
    op.drop_constraint('fk_journals_customer_receivable_account', 'journals', type_='foreignkey')
    
    # Drop columns
    op.drop_column('journals', 'currency_exchange_account_id')
    op.drop_column('journals', 'bank_charges_account_id')
    op.drop_column('journals', 'cash_difference_account_id')
    op.drop_column('journals', 'supplier_payable_account_id')
    op.drop_column('journals', 'customer_receivable_account_id')
