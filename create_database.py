#!/usr/bin/env python3
"""
Script para crear la base de datos PostgreSQL
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# Configuración de conexión
POSTGRES_SERVER = "localhost"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "api_contable_dev2"
POSTGRES_PORT = 5432

def create_database():
    """Crear la base de datos si no existe"""
    try:
        # Conectar a PostgreSQL (base de datos default 'postgres')
        print(f"Conectando a PostgreSQL en {POSTGRES_SERVER}:{POSTGRES_PORT}...")
        print(f"Usuario: {POSTGRES_USER}")
        
        conn = psycopg2.connect(
            host=POSTGRES_SERVER,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database="api_contable_dev2"  # Conectar a la DB por defecto
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar si la base de datos ya existe
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (POSTGRES_DB,)
        )
        
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ La base de datos '{POSTGRES_DB}' ya existe.")
        else:
            # Crear la base de datos
            print(f"📦 Creando base de datos '{POSTGRES_DB}'...")
            cursor.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
            print(f"✅ Base de datos '{POSTGRES_DB}' creada exitosamente.")
        
        cursor.close()
        conn.close()
        
        # Verificar conexión a la nueva base de datos
        print(f"🔗 Verificando conexión a '{POSTGRES_DB}'...")
        test_conn = psycopg2.connect(
            host=POSTGRES_SERVER,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        test_conn.close()
        print(f"✅ Conexión exitosa a '{POSTGRES_DB}'!")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        print("Verifica que PostgreSQL esté ejecutándose y las credenciales sean correctas.")
        return False
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Configurando base de datos PostgreSQL...")
    print("-" * 50)
    
    if create_database():
        print("\n🎉 Base de datos configurada correctamente!")
        print("Ahora puedes ejecutar las migraciones de Alembic.")
    else:
        print("\n💥 Error al configurar la base de datos.")
        sys.exit(1)
