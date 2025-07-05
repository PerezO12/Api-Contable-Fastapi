#!/usr/bin/env python3
"""
Script para agregar campos de configuración de cuentas faltantes en journals
"""
import asyncio
import os
import sys

# Agregar el path de la aplicación
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.database import get_async_db
from sqlalchemy import text

async def add_missing_journal_fields():
    """Agrega campos de configuración de cuentas faltantes a la tabla journals"""
    
    async for db in get_async_db():
        print("🔧 Agregando campos de configuración de cuentas faltantes en journals...")
        
        try:
            # Verificar si los campos ya existen
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'journals' 
                AND column_name IN (
                    'default_debit_account_id',
                    'default_credit_account_id'
                )
            """)
            
            result = await db.execute(check_query)
            existing_columns = [row[0] for row in result.fetchall()]
            
            if len(existing_columns) >= 2:
                print(f"ℹ️ Los campos ya existen: {existing_columns}")
                print("✅ Los campos de configuración ya están presentes")
                return True
            
            # Agregar campos nuevos
            alter_queries = [
                """
                ALTER TABLE journals 
                ADD COLUMN default_debit_account_id UUID REFERENCES accounts(id)
                """,
                """
                ALTER TABLE journals 
                ADD COLUMN default_credit_account_id UUID REFERENCES accounts(id)
                """
            ]
            
            for i, query in enumerate(alter_queries, 1):
                if i == 1 and 'default_debit_account_id' in existing_columns:
                    print(f"📝 Saltando alteración {i}/{len(alter_queries)} - ya existe...")
                    continue
                if i == 2 and 'default_credit_account_id' in existing_columns:
                    print(f"📝 Saltando alteración {i}/{len(alter_queries)} - ya existe...")
                    continue
                print(f"📝 Ejecutando alteración {i}/{len(alter_queries)}...")
                await db.execute(text(query))
            
            await db.commit()
            print("🎉 Campos agregados exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error agregando campos: {str(e)}")
            await db.rollback()
            return False
        
        break

if __name__ == "__main__":
    success = asyncio.run(add_missing_journal_fields())
    sys.exit(0 if success else 1)
