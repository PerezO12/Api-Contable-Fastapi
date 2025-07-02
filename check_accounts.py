#!/usr/bin/env python3
"""
Script para verificar cuentas bancarias disponibles
"""

import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models.account import Account, AccountType
from sqlalchemy.future import select

async def main():
    """Función principal"""
    async with AsyncSessionLocal() as db:
        try:
            # Buscar cuentas bancarias
            result = await db.execute(
                select(Account).where(Account.account_type == AccountType.ACTIVO)
                .order_by(Account.code)
            )
            accounts = result.scalars().all()
            
            print(f'Cuentas de tipo ACTIVO encontradas: {len(accounts)}')
            
            # Filtrar las que parecen bancarias
            bank_accounts = []
            for account in accounts:
                if any(keyword in account.name.lower() for keyword in ['banco', 'bancos', 'cuenta bancaria', 'efectivo', 'caja']):
                    bank_accounts.append(account)
                    print(f'- {account.code} - {account.name} (ID: {account.id})')
            
            print(f'\nTotal de cuentas que parecen bancarias: {len(bank_accounts)}')
            
            if bank_accounts:
                print(f'\nSugerencia: Usar cuenta {bank_accounts[0].code} - {bank_accounts[0].name}')
                print(f'ID para actualizar: {bank_accounts[0].id}')
                    
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
