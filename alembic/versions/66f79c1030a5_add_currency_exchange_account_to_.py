"""add_currency_exchange_account_to_company_settings

Revision ID: 66f79c1030a5
Revises: 495be228e719
Create Date: 2025-07-06 16:37:49.007852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66f79c1030a5'
down_revision: Union[str, None] = '495be228e719'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the missing currency exchange account field
    op.add_column('company_settings', sa.Column(
        'default_currency_exchange_account_id',
        sa.UUID(),
        nullable=True,
        comment="Cuenta para diferencias de cambio"
    ))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_company_settings_currency_exchange_account',
        'company_settings',
        'accounts',
        ['default_currency_exchange_account_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_company_settings_currency_exchange_account', 'company_settings', type_='foreignkey')
    
    # Drop the column
    op.drop_column('company_settings', 'default_currency_exchange_account_id')