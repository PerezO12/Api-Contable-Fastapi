#!/usr/bin/env python3
"""
Script para crear un usuario administrador por defecto
Ejecutar: python create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.config import settings


async def create_admin_user():
    """Crear usuario administrador usando las credenciales del .env"""
    print("🔧 Creando usuario administrador por defecto...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Usar el servicio de auth para crear el admin
            auth_service = AuthService(db)
            admin_user = await auth_service.create_default_admin_user()
            
            if admin_user:
                print("✅ Usuario administrador creado exitosamente!")
                print(f"   📧 Email: {admin_user.email}")
                print(f"   👤 Nombre: {admin_user.full_name}")
                print(f"   🔑 Contraseña: {settings.DEFAULT_ADMIN_PASSWORD}")
                print(f"   🛡️  Rol: {admin_user.role.value}")
                print("\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login!")
            else:
                print("ℹ️  No se creó el usuario administrador:")
                print("   - Ya existe un administrador en el sistema, o")
                print("   - El email configurado ya está en uso")
                
                # Verificar si existe admin
                from sqlalchemy import select
                from app.models.user import User, UserRole
                
                result = await db.execute(
                    select(User).where(User.role == UserRole.ADMIN)
                )
                existing_admin = result.scalar_one_or_none()
                
                if existing_admin:
                    print(f"   📧 Admin existente: {existing_admin.email}")
                
        except Exception as e:
            print(f"❌ Error creando usuario administrador: {e}")
            return False
    
    return True


async def main():
    """Función principal"""
    print("=" * 60)
    print("🏦 SISTEMA CONTABLE - CREACIÓN DE ADMINISTRADOR")
    print("=" * 60)
    print()
    
    # Mostrar configuración actual
    print("📋 Configuración actual:")
    print(f"   📧 Email: {settings.DEFAULT_ADMIN_EMAIL}")
    print(f"   👤 Nombre: {settings.DEFAULT_ADMIN_FULL_NAME}")
    print(f"   🔑 Contraseña: {'*' * len(settings.DEFAULT_ADMIN_PASSWORD)}")
    print()
    
    # Confirmar creación
    response = input("¿Deseas crear el usuario administrador? (y/N): ")
    if response.lower() not in ['y', 'yes', 'sí', 'si']:
        print("❌ Operación cancelada")
        return
    
    # Crear usuario
    success = await create_admin_user()
    
    print()
    if success:
        print("🎉 ¡Proceso completado!")
        print("📚 Puedes usar estas credenciales para hacer login en /docs")
    else:
        print("💥 Proceso falló. Revisa los logs arriba.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
