#!/usr/bin/env python3
"""
Script para crear las cuentas de impuestos por defecto
Ejecutar: python create_default_tax_accounts.py
"""
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.account import Account, AccountType, AccountCategory
from app.models.user import User, UserRole
from app.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir las cuentas de impuestos por defecto
DEFAULT_TAX_ACCOUNTS = [
    {
        'code': '2.1.4.01',
        'name': 'ICMS por Pagar',
        'description': 'Cuenta para control de ICMS por pagar/deducible',
        'account_type': AccountType.PASIVO.value,
        'category': AccountCategory.IMPUESTOS.value,
    },
    {
        'code': '2.1.4.02',
        'name': 'IPI por Pagar',
        'description': 'Cuenta para control de IPI por pagar/deducible',
        'account_type': AccountType.PASIVO.value,
        'category': AccountCategory.IMPUESTOS.value,
    },
    {
        'code': '2.1.4.03',
        'name': 'PIS por Pagar',
        'description': 'Cuenta para control de PIS por pagar/deducible',
        'account_type': AccountType.PASIVO.value,
        'category': AccountCategory.IMPUESTOS.value,
    },
    {
        'code': '2.1.4.04',
        'name': 'COFINS por Pagar',
        'description': 'Cuenta para control de COFINS por pagar/deducible',
        'account_type': AccountType.PASIVO.value,
        'category': AccountCategory.IMPUESTOS.value,
    }
]

async def create_default_tax_accounts():
    """Crear las cuentas de impuestos por defecto si no existen"""
    async with AsyncSessionLocal() as session:
        session: AsyncSession
        
        # Verificar y crear cada cuenta
        for account_data in DEFAULT_TAX_ACCOUNTS:
            # Verificar si la cuenta ya existe
            stmt = select(Account).where(Account.code == account_data['code'])
            result = await session.execute(stmt)
            existing_account = result.scalar_one_or_none()
            
            if not existing_account:
                # Crear la cuenta
                new_account = Account(
                    id=uuid4(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    **account_data,
                    # Configuración adicional
                    level=1,
                    is_active=True,
                    allows_movements=True,
                    requires_third_party=False,
                    requires_cost_center=False,
                    allows_reconciliation=True,
                    balance=0,
                    debit_balance=0,
                    credit_balance=0
                )
                session.add(new_account)
        
        try:
            await session.commit()
            logger.info("✅ Cuentas de impuestos creadas exitosamente")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error al crear cuentas de impuestos: {str(e)}")
            raise

async def main():
    """Función principal"""
    print("=" * 60)
    print("🏦 SISTEMA CONTABLE - CREACIÓN DE CUENTAS DE IMPUESTOS")
    print("=" * 60)
    print("\n📋 Configuración de cuentas:")
    for account in DEFAULT_TAX_ACCOUNTS[:3]:  # Solo mostrar las primeras 3 cuentas
        print(f"   📊 {account['name'].split()[0]}: {account['code']} - {account['name']}")
    print()
    
    response = input("¿Deseas crear las cuentas de impuestos? (y/N): ")
    if response.lower() == 'y':
        await create_default_tax_accounts()
    else:
        print("❌ Operación cancelada")

if __name__ == "__main__":
    asyncio.run(main()) 