#!/usr/bin/env python
"""
Script para depurar el error de importación - versión simplificada
"""
try:
    print("1. Importando config...")
    from app.config import settings
    print("✅ Config importado")
    
    print("2. Importando database...")
    from app.database import async_engine
    print("✅ Database importado")
    
    print("3. Importando modelos...")
    from app.models import user
    print("✅ Modelos importados")
    
    print("4. Importando schemas...")
    from app.schemas import user as user_schema
    print("✅ Schemas importados")
    
    print("5. Importando servicios...")
    from app.services import auth_service
    print("✅ Servicios importados")
    
    print("6. Importando API deps...")
    from app.api import deps
    print("✅ API deps importados")
    
    print("7. Importando routers...")
    from app.api.v1 import auth
    print("✅ Auth router importado")
    
    print("8. Importando aplicación principal...")
    from app.main import app
    print("✅ ¡Todo importado correctamente!")
    
except Exception as e:
    print(f"❌ Error en paso: {e}")
    import traceback
    traceback.print_exc()
