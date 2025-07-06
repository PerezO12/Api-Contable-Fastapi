#!/usr/bin/env python3
"""
Script para verificar la estructura de la base de datos PostgreSQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def check_db_structure():
    """Verifica la estructura de la base de datos PostgreSQL"""
    # Usar la configuración real
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Verificar si la tabla company_settings existe
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename = 'company_settings'"))
        if result.fetchone():
            print("✓ Tabla company_settings existe")
            
            # Verificar estructura de la tabla
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'company_settings'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("\nColumnas en company_settings:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                
            # Verificar si los campos que necesitamos existen
            column_names = [col[0] for col in columns]
            
            if 'default_sales_income_account_id' in column_names:
                print("✓ Campo default_sales_income_account_id existe")
            else:
                print("✗ Campo default_sales_income_account_id NO existe")
                
            if 'default_purchase_expense_account_id' in column_names:
                print("✓ Campo default_purchase_expense_account_id existe")
            else:
                print("✗ Campo default_purchase_expense_account_id NO existe")
        else:
            print("✗ Tabla company_settings NO existe")
            
        # Verificar estructura de accounts
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename = 'accounts'"))
        if result.fetchone():
            print("\n✓ Tabla accounts existe")
            
            # Contar cuentas por tipo
            result = conn.execute(text("SELECT account_type, COUNT(*) FROM accounts GROUP BY account_type"))
            print("\nCuentas por tipo:")
            for row in result.fetchall():
                print(f"  - {row[0]}: {row[1]} cuentas")
        else:
            print("\n✗ Tabla accounts NO existe")

if __name__ == "__main__":
    check_db_structure()
