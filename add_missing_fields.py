#!/usr/bin/env python3
"""
Script para agregar manualmente los campos faltantes a company_settings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def add_missing_fields():
    """Agregar campos faltantes a la tabla company_settings"""
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Verificar si los campos ya existen
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'company_settings' 
            AND column_name IN ('default_sales_income_account_id', 'default_purchase_expense_account_id')
        """))
        existing_fields = [row[0] for row in result.fetchall()]
        
        # Agregar campo default_sales_income_account_id si no existe
        if 'default_sales_income_account_id' not in existing_fields:
            print("Agregando campo default_sales_income_account_id...")
            conn.execute(text("""
                ALTER TABLE company_settings 
                ADD COLUMN default_sales_income_account_id UUID
            """))
            conn.execute(text("""
                COMMENT ON COLUMN company_settings.default_sales_income_account_id 
                IS 'Cuenta de ingresos por ventas por defecto'
            """))
            print("✓ Campo default_sales_income_account_id agregado")
        else:
            print("✓ Campo default_sales_income_account_id ya existe")
        
        # Agregar campo default_purchase_expense_account_id si no existe
        if 'default_purchase_expense_account_id' not in existing_fields:
            print("Agregando campo default_purchase_expense_account_id...")
            conn.execute(text("""
                ALTER TABLE company_settings 
                ADD COLUMN default_purchase_expense_account_id UUID
            """))
            conn.execute(text("""
                COMMENT ON COLUMN company_settings.default_purchase_expense_account_id 
                IS 'Cuenta de gastos por compras por defecto'
            """))
            print("✓ Campo default_purchase_expense_account_id agregado")
        else:
            print("✓ Campo default_purchase_expense_account_id ya existe")
        
        # Agregar las foreign keys
        if 'default_sales_income_account_id' not in existing_fields:
            try:
                conn.execute(text("""
                    ALTER TABLE company_settings 
                    ADD CONSTRAINT fk_company_settings_default_sales_income_account 
                    FOREIGN KEY (default_sales_income_account_id) REFERENCES accounts(id)
                """))
                print("✓ Foreign key para default_sales_income_account_id agregada")
            except Exception as e:
                print(f"! Error agregando foreign key para sales income: {e}")
        
        if 'default_purchase_expense_account_id' not in existing_fields:
            try:
                conn.execute(text("""
                    ALTER TABLE company_settings 
                    ADD CONSTRAINT fk_company_settings_default_purchase_expense_account 
                    FOREIGN KEY (default_purchase_expense_account_id) REFERENCES accounts(id)
                """))
                print("✓ Foreign key para default_purchase_expense_account_id agregada")
            except Exception as e:
                print(f"! Error agregando foreign key para purchase expense: {e}")
        
        # Hacer commit de los cambios
        conn.commit()
        print("\n✅ Campos agregados exitosamente")

if __name__ == "__main__":
    add_missing_fields()
