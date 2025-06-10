#!/usr/bin/env python
"""
Script básico para verificar configuración
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Verificando configuración...")
    from app.config import settings
    print(f"DB_HOST: {settings.DB_HOST}")
    print(f"DB_NAME: {settings.DB_NAME}")
    print(f"DB_USER: {settings.DB_USER}")
    print(f"DATABASE_URI: {settings.SQLALCHEMY_DATABASE_URI}")
    print("✅ Configuración OK")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
