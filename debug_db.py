#!/usr/bin/env python3
"""
Script para debuggear la conexión a PostgreSQL
"""
import sys
import os

# Agregar el path del proyecto
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.core.config import settings

def main():
    print("🔍 Debuggeando configuración de base de datos...")
    print("-" * 60)
    
    print(f"POSTGRES_SERVER: {settings.POSTGRES_SERVER}")
    print(f"POSTGRES_USER: {settings.POSTGRES_USER}")
    print(f"POSTGRES_PASSWORD: {'*' * len(settings.POSTGRES_PASSWORD)}")
    print(f"POSTGRES_DB: {settings.POSTGRES_DB}")
    print(f"POSTGRES_PORT: {settings.POSTGRES_PORT}")
    
    print("\n📝 URLs de conexión:")
    print(f"Sync URL: {settings.SQLALCHEMY_DATABASE_URI}")
    print(f"Async URL: {settings.ASYNC_SQLALCHEMY_DATABASE_URI}")
    
    print("\n🔍 Información de encoding:")
    print(f"Default encoding: {sys.getdefaultencoding()}")
    print(f"Filesystem encoding: {sys.getfilesystemencoding()}")
    
    # Verificar si hay caracteres problemáticos
    url = settings.SQLALCHEMY_DATABASE_URI
    print(f"\n📊 Análisis de URL (longitud: {len(url)}):")
    for i, char in enumerate(url):
        if ord(char) > 127:
            print(f"Carácter no-ASCII en posición {i}: {repr(char)} (código {ord(char)})")
    
    # Intentar conexión con psycopg2 directamente
    try:
        import psycopg2
        print("\n🔗 Intentando conexión directa con psycopg2...")
        
        # URL sin encoding especial
        simple_url = f"host={settings.POSTGRES_SERVER} port={settings.POSTGRES_PORT} user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} dbname={settings.POSTGRES_DB}"
        print(f"Conexión simple: {simple_url}")
        
        conn = psycopg2.connect(simple_url)
        print("✅ Conexión exitosa con psycopg2!")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error con psycopg2: {e}")
    
    # Intentar con SQLAlchemy
    try:
        from sqlalchemy import create_engine
        print("\n🔗 Intentando conexión con SQLAlchemy...")
        
        # URL escapada correctamente
        escaped_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        print(f"URL SQLAlchemy: {escaped_url}")
        
        engine = create_engine(escaped_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Conexión exitosa con SQLAlchemy!")
            
    except Exception as e:
        print(f"❌ Error con SQLAlchemy: {e}")

if __name__ == "__main__":
    main()
