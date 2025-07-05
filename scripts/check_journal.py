#!/usr/bin/env python3
"""
Script para verificar el estado de los journals de banco
"""

import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models.journal import Journal
from sqlalchemy.future import select

async def main():
    """Función principal"""
    async with AsyncSessionLocal() as db:
        try:
            # Buscar el journal que está causando problemas
            result = await db.execute(
                select(Journal).where(Journal.name.ilike('%Diario de Banco Principal%'))
            )
            journal = result.scalar_one_or_none()
            
            if journal:
                print(f'Journal encontrado:')
                print(f'ID: {journal.id}')
                print(f'Nombre: {journal.name}')
                print(f'Código: {journal.code}')
                print(f'Tipo: {journal.type}')
                print(f'Cuenta por defecto ID: {journal.default_account_id}')
                print(f'Activo: {journal.is_active}')
            else:
                print('No se encontró el journal con ese nombre')
                
                # Buscar todos los journals de tipo bank
                result = await db.execute(
                    select(Journal).where(Journal.type == 'bank')
                )
                bank_journals = result.scalars().all()
                print(f'\nJournals de tipo bank encontrados: {len(bank_journals)}')
                for j in bank_journals:
                    print(f'- {j.name} (ID: {j.id}) - Cuenta por defecto: {j.default_account_id}')
                    
                # Buscar cualquier journal que contenga "banco"
                result = await db.execute(
                    select(Journal).where(Journal.name.ilike('%banco%'))
                )
                all_bank_journals = result.scalars().all()
                print(f'\nTodos los journals que contienen "banco": {len(all_bank_journals)}')
                for j in all_bank_journals:
                    print(f'- {j.name} (ID: {j.id}) - Tipo: {j.type} - Cuenta por defecto: {j.default_account_id}')
                    
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
