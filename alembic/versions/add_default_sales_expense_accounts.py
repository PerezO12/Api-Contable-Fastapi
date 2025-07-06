"""add default sales and expense accounts to company settings

Revision ID: add_default_sales_expense_accounts_001
Revises: a7a33b0d5323
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers
revision = 'add_default_sales_001'
down_revision = 'add_payment_accounts_to_journals'
branch_labels = None
depends_on = None


def upgrade():
    # Add default sales income account field
    op.add_column('company_settings', 
                  sa.Column('default_sales_income_account_id', 
                           sa.UUID(), 
                           nullable=True,
                           comment="Cuenta de ingresos por ventas por defecto"))
    
    # Add default purchase expense account field
    op.add_column('company_settings', 
                  sa.Column('default_purchase_expense_account_id', 
                           sa.UUID(), 
                           nullable=True,
                           comment="Cuenta de gastos por compras por defecto"))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_company_settings_default_sales_income_account',
                         'company_settings',
                         'accounts',
                         ['default_sales_income_account_id'],
                         ['id'])
    
    op.create_foreign_key('fk_company_settings_default_purchase_expense_account',
                         'company_settings',
                         'accounts',
                         ['default_purchase_expense_account_id'],
                         ['id'])


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_company_settings_default_sales_income_account',
                      'company_settings',
                      type_='foreignkey')
    
    op.drop_constraint('fk_company_settings_default_purchase_expense_account',
                      'company_settings',
                      type_='foreignkey')
    
    # Drop columns
    op.drop_column('company_settings', 'default_sales_income_account_id')
    op.drop_column('company_settings', 'default_purchase_expense_account_id')
