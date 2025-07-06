#!/usr/bin/env python3
"""
Script para configurar cuentas por defecto en CompanySettings
Busca automáticamente cuentas de ingresos y gastos apropiadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.account import Account, AccountType
from app.models.company_settings import CompanySettings
from app.config import Settings

def setup_default_accounts():
    """Configura las cuentas por defecto en CompanySettings"""
    config = Settings()
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Obtener o crear configuración de empresa
        settings = CompanySettings.get_or_create_default(session)
        
        print(f"Configurando cuentas por defecto para empresa: {settings.company_name}")
        
        # Buscar cuenta de ingresos por ventas por defecto
        if not settings.default_sales_income_account_id:
            print("\n=== Buscando cuenta de ingresos por ventas por defecto ===")
            
            # Patrones comunes para ingresos por ventas
            income_patterns = ['411', '4100', '4110', '4111', '4135', '41100', '41110']
            
            sales_income_account = None
            for pattern in income_patterns:
                # Buscar coincidencia exacta
                account = session.query(Account).filter(
                    Account.code == pattern,
                    Account.account_type == AccountType.INCOME,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                
                if account:
                    sales_income_account = account
                    print(f"  Encontrada cuenta exacta: {account.code} - {account.name}")
                    break
                
                # Buscar que comience con el patrón
                account = session.query(Account).filter(
                    Account.code.like(f"{pattern}%"),
                    Account.account_type == AccountType.INCOME,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                
                if account:
                    sales_income_account = account
                    print(f"  Encontrada cuenta por patrón: {account.code} - {account.name}")
                    break
            
            if not sales_income_account:
                # Buscar cualquier cuenta de ingresos activa
                sales_income_account = session.query(Account).filter(
                    Account.account_type == AccountType.INCOME,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).order_by(Account.code).first()
                
                if sales_income_account:
                    print(f"  Usando primera cuenta de ingresos: {sales_income_account.code} - {sales_income_account.name}")
            
            if sales_income_account:
                settings.default_sales_income_account_id = sales_income_account.id
                print(f"  ✓ Cuenta de ingresos por ventas configurada: {sales_income_account.code}")
            else:
                print("  ✗ No se encontró cuenta de ingresos por ventas")
        else:
            print("  ✓ Cuenta de ingresos por ventas ya configurada")
        
        # Buscar cuenta de gastos por compras por defecto
        if not settings.default_purchase_expense_account_id:
            print("\n=== Buscando cuenta de gastos por compras por defecto ===")
            
            # Patrones comunes para gastos por compras
            expense_patterns = ['511', '5100', '5110', '5111', '51100', '51110']
            
            purchase_expense_account = None
            for pattern in expense_patterns:
                # Buscar coincidencia exacta
                account = session.query(Account).filter(
                    Account.code == pattern,
                    Account.account_type == AccountType.EXPENSE,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                
                if account:
                    purchase_expense_account = account
                    print(f"  Encontrada cuenta exacta: {account.code} - {account.name}")
                    break
                
                # Buscar que comience con el patrón
                account = session.query(Account).filter(
                    Account.code.like(f"{pattern}%"),
                    Account.account_type == AccountType.EXPENSE,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).first()
                
                if account:
                    purchase_expense_account = account
                    print(f"  Encontrada cuenta por patrón: {account.code} - {account.name}")
                    break
            
            if not purchase_expense_account:
                # Buscar cualquier cuenta de gastos activa
                purchase_expense_account = session.query(Account).filter(
                    Account.account_type == AccountType.EXPENSE,
                    Account.is_active == True,
                    Account.allows_movements == True
                ).order_by(Account.code).first()
                
                if purchase_expense_account:
                    print(f"  Usando primera cuenta de gastos: {purchase_expense_account.code} - {purchase_expense_account.name}")
            
            if purchase_expense_account:
                settings.default_purchase_expense_account_id = purchase_expense_account.id
                print(f"  ✓ Cuenta de gastos por compras configurada: {purchase_expense_account.code}")
            else:
                print("  ✗ No se encontró cuenta de gastos por compras")
        else:
            print("  ✓ Cuenta de gastos por compras ya configurada")
        
        # Guardar cambios
        session.commit()
        
        print("\n=== Resumen de configuración ===")
        print(f"Empresa: {settings.company_name}")
        print(f"Moneda: {settings.currency_code}")
        
        if settings.default_sales_income_account_id:
            account = session.query(Account).get(settings.default_sales_income_account_id)
            if account:
                print(f"Cuenta ingresos por ventas: {account.code} - {account.name}")
        
        if settings.default_purchase_expense_account_id:
            account = session.query(Account).get(settings.default_purchase_expense_account_id)
            if account:
                print(f"Cuenta gastos por compras: {account.code} - {account.name}")
        
        print("\n✅ Configuración completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    setup_default_accounts()
