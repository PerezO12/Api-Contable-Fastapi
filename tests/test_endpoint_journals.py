#!/usr/bin/env python3
"""
Script para probar el endpoint completo de journals como lo hace el frontend
"""
import asyncio
import sys
import os
import json

# Añadir el directorio padre al path para importar los módulos de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.api.v1.journals import get_journals
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.journal import JournalType

async def test_endpoint_simulation():
    """Simula la llamada al endpoint como lo hace el frontend"""
    
    # Crear conexión a la base de datos
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
            # Simular parámetros del endpoint
            type_param = None
            is_active = None
            search = None
            skip = 0
            limit = 50
            order_by = "name"
            order_dir = "asc"
            
            # Obtener un usuario para simular autenticación
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.is_active == True).limit(1)
            )
            current_user = result.scalar_one_or_none()
            
            if not current_user:
                print("Error: No se encontró un usuario activo")
                return
            
            # Llamar a la función del endpoint directamente
            try:
                response = await get_journals(
                    type=type_param,
                    is_active=is_active,
                    search=search,
                    skip=skip,
                    limit=limit,
                    order_by=order_by,
                    order_dir=order_dir,
                    db=session,
                    current_user=current_user
                )
                
                print("✅ Endpoint funciona correctamente")
                print(f"Total items: {response.total}")
                print(f"Items en esta página: {len(response.items)}")
                print("-" * 50)
                
                for journal in response.items:
                    print(f"Journal: {journal.name}")
                    if journal.default_account:
                        print(f"  Cuenta: {journal.default_account.code} - {journal.default_account.name}")
                    else:
                        print("  Sin cuenta por defecto")
                    print()
                    
            except Exception as e:
                print(f"❌ Error en el endpoint: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"Error de conexión: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_endpoint_simulation())
