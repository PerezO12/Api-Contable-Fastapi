#!/usr/bin/env python3
"""
Script para actualizar la cuenta por defecto del journal de banco
"""

import asyncio
import uuid
from app.database import AsyncSessionLocal
from app.models.journal import Journal
from sqlalchemy.future import select

async def main():
    """Función principal"""
    async with AsyncSessionLocal() as db:
        try:
            # Buscar el journal de banco
            result = await db.execute(
                select(Journal).where(Journal.name.ilike('%Diario de Banco Principal%'))
            )
            journal = result.scalar_one_or_none()
            
            if not journal:
                print('No se encontró el journal')
                return
            
            # ID de la cuenta bancaria encontrada
            bank_account_id = uuid.UUID('fa14c054-04d8-4ffc-9df3-e500d2041cb1')
            
            print(f'Actualizando journal: {journal.name}')
            print(f'Cuenta por defecto actual: {journal.default_account_id}')
            print(f'Nueva cuenta por defecto: {bank_account_id}')
            
            # Actualizar la cuenta por defecto
            journal.default_account_id = bank_account_id
            
            await db.commit()
            await db.refresh(journal)
            
            print(f'✅ Journal actualizado exitosamente')
            print(f'Cuenta por defecto: {journal.default_account_id}')
                    
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())
