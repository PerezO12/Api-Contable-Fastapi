#!/usr/bin/env python3
"""
Script para probar el endpoint de journals con las cuentas por defecto
"""
import asyncio
import sys
import os

# Añadir el directorio padre al path para importar los módulos de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.services.journal_service import JournalService
from app.schemas.journal import JournalFilter

async def test_journals_with_accounts():
    """Prueba la obtención de journals con cuentas por defecto"""    # Crear conexión a la base de datos
    engine = create_async_engine(
        settings.database_connection_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
      async_session = async_sessionmaker(
        bind=engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            journal_service = JournalService(session)
            
            # Obtener journals con filtros vacíos
            filters = JournalFilter(type=None, is_active=None, search=None)
            journals_data = await journal_service.get_journals_list(
                filters=filters,
                skip=0,
                limit=10
            )
            
            print(f"Se encontraron {len(journals_data)} journals:")
            print("-" * 50)
            
            for journal_data in journals_data:
                print(f"ID: {journal_data['id']}")
                print(f"Nombre: {journal_data['name']}")
                print(f"Código: {journal_data['code']}")
                print(f"Tipo: {journal_data['type']}")
                print(f"Total asientos: {journal_data['total_journal_entries']}")
                
                if journal_data.get('default_account'):
                    account = journal_data['default_account']
                    print(f"Cuenta por defecto: {account.code} - {account.name}")
                else:
                    print("Cuenta por defecto: Sin cuenta")
                
                print("-" * 30)
                
    except Exception as e:
        print(f"Error al obtener journals: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_journals_with_accounts())
