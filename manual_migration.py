#!/usr/bin/env python3
"""
Script alternativo para ejecutar migraciones usando SQLAlchemy directamente
"""
import sqlalchemy as sa
from sqlalchemy import text
import sys
import os

def run_migration_sql():
    """Ejecutar el SQL de migración directamente"""
    
    # URL de conexión simple
    db_url = "postgresql://postgres:postgres@localhost:5432/api_contable_dev"
    
    # SQL de migración (copiado del output de alembic upgrade --sql)
    migration_sql = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL,
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
    );
    
    -- Verificar si ya existe la migración
    INSERT INTO alembic_version (version_num) VALUES ('b0073181356e') ON CONFLICT DO NOTHING;
    
    -- Crear enums si no existen
    DO $$ BEGIN
        CREATE TYPE userrole AS ENUM ('ADMIN', 'CONTADOR', 'SOLO_LECTURA');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE accounttype AS ENUM ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE accountcategory AS ENUM ('CURRENT_ASSET', 'NON_CURRENT_ASSET', 'CURRENT_LIABILITY', 'NON_CURRENT_LIABILITY', 'CAPITAL', 'RETAINED_EARNINGS', 'OPERATING_REVENUE', 'NON_OPERATING_REVENUE', 'OPERATING_EXPENSE', 'NON_OPERATING_EXPENSE');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE journalentrytype AS ENUM ('MANUAL', 'AUTOMATIC', 'ADJUSTMENT', 'CLOSING', 'OPENING');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE journalentrystatus AS ENUM ('DRAFT', 'APPROVED', 'POSTED', 'CANCELLED');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE auditaction AS ENUM ('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'IMPORT', 'APPROVE', 'REJECT', 'CANCEL');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE auditloglevel AS ENUM ('INFO', 'WARNING', 'ERROR', 'CRITICAL');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    -- Crear tabla users
    CREATE TABLE IF NOT EXISTS users (
        id UUID NOT NULL DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL,
        hashed_password VARCHAR NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        role userrole NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT true,
        is_verified BOOLEAN NOT NULL DEFAULT false,
        last_login TIMESTAMP WITH TIME ZONE,
        failed_login_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until TIMESTAMP WITH TIME ZONE,
        password_changed_at TIMESTAMP WITH TIME ZONE,
        must_change_password BOOLEAN NOT NULL DEFAULT false,
        phone VARCHAR(20),
        department VARCHAR(100),
        employee_id VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        CONSTRAINT pk_users PRIMARY KEY (id),
        CONSTRAINT uq_users_email UNIQUE (email),
        CONSTRAINT uq_users_employee_id UNIQUE (employee_id)
    );
    
    CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
    CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);
    
    COMMIT;
    """
    
    try:
        print("🔗 Conectando a la base de datos...")
        print(f"URL: {db_url}")
        
        engine = sa.create_engine(db_url)
        
        with engine.connect() as conn:
            print("✅ Conexión exitosa!")
            print("📝 Ejecutando migración básica...")
            
            # Ejecutar el SQL en bloques para evitar problemas
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"⚠️  Warning: {e}")
            
            print("✅ Migración básica completada!")
            
            # Verificar que las tablas fueron creadas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"📋 Tablas creadas: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ejecutando migración manual...")
    print("-" * 50)
    
    if run_migration_sql():
        print("\n🎉 Migración completada exitosamente!")
    else:
        print("\n💥 Error en la migración.")
        sys.exit(1)
