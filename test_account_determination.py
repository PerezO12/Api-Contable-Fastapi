#!/usr/bin/env python3
"""
Test para verificar que la determinación de cuentas funciona correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.account import Account, AccountType
from app.models.company_settings import CompanySettings
from app.models.invoice import Invoice, InvoiceLine, InvoiceType
from app.models.third_party import ThirdParty
from app.services.account_determination_service import AccountDeterminationService
from app.config import Settings
from decimal import Decimal

def test_account_determination():
    """Test completo de determinación de cuentas"""
    config = Settings()
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=== Test de Determinación de Cuentas ===")
        
        # Crear servicio de determinación de cuentas
        account_service = AccountDeterminationService(session)
        
        # Verificar configuración de empresa
        settings = account_service.get_company_settings()
        if settings:
            print(f"\nConfiguración de empresa: {settings.company_name}")
            
            if settings.default_sales_income_account_id:
                sales_account = session.query(Account).get(settings.default_sales_income_account_id)
                if sales_account:
                    print(f"Cuenta ingresos por ventas: {sales_account.code} - {sales_account.name}")
            
            if settings.default_purchase_expense_account_id:
                expense_account = session.query(Account).get(settings.default_purchase_expense_account_id)
                if expense_account:
                    print(f"Cuenta gastos por compras: {expense_account.code} - {expense_account.name}")
        else:
            print("\n✗ No se encontró configuración de empresa")
        
        # Test 1: Obtener cuenta de ingresos por ventas por defecto
        print("\n=== Test 1: Cuenta de ingresos por ventas ===")
        sales_income_account = account_service._get_default_sales_income_account()
        
        if sales_income_account:
            print(f"✓ Cuenta encontrada: {sales_income_account.code} - {sales_income_account.name}")
            print(f"  Tipo: {sales_income_account.account_type}")
            print(f"  Activa: {sales_income_account.is_active}")
            print(f"  Permite movimientos: {sales_income_account.allows_movements}")
        else:
            print("✗ No se encontró cuenta de ingresos por ventas")
        
        # Test 2: Obtener cuenta de gastos por compras por defecto
        print("\n=== Test 2: Cuenta de gastos por compras ===")
        purchase_expense_account = account_service._get_default_purchase_expense_account()
        
        if purchase_expense_account:
            print(f"✓ Cuenta encontrada: {purchase_expense_account.code} - {purchase_expense_account.name}")
            print(f"  Tipo: {purchase_expense_account.account_type}")
            print(f"  Activa: {purchase_expense_account.is_active}")
            print(f"  Permite movimientos: {purchase_expense_account.allows_movements}")
        else:
            print("✗ No se encontró cuenta de gastos por compras")
        
        # Test 3: Crear factura de prueba y determinar cuentas
        print("\n=== Test 3: Determinación de cuentas para factura ===")
        
        # Obtener un tercero existente
        third_party = session.query(ThirdParty).first()
        if not third_party:
            print("✗ No se encontró tercero para prueba")
            return
        
        # Crear factura de prueba (sin guardar en BD)
        test_invoice = Invoice(
            invoice_type=InvoiceType.CUSTOMER_INVOICE,
            number="TEST-001",
            third_party_id=third_party.id,
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("19.00"),
            total_amount=Decimal("119.00")
        )
        
        # Simular relación con tercero
        test_invoice.third_party = third_party
        
        # Crear línea de factura de prueba
        test_line = InvoiceLine(
            sequence=1,
            description="Producto de prueba",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("0.00")
        )
        
        # Simular relación con factura
        test_line.invoice = test_invoice
        test_invoice.lines = [test_line]
        
        # Determinar cuentas
        try:
            accounts = account_service.determine_accounts_for_invoice(test_invoice)
            
            print(f"✓ Determinación exitosa:")
            print(f"  Cuenta tercero: {accounts['third_party_account']['account_code']} - {accounts['third_party_account']['account_name']}")
            print(f"  Fuente: {accounts['third_party_account']['source']}")
            
            for i, line_account in enumerate(accounts['line_accounts']):
                print(f"  Línea {i+1}: {line_account['account_code']} - {line_account['account_name']}")
                print(f"    Fuente: {line_account['source']}")
            
            if accounts['tax_accounts']:
                for tax_account in accounts['tax_accounts']:
                    print(f"  Impuesto: {tax_account['account_code']} - {tax_account['account_name']}")
            
        except Exception as e:
            print(f"✗ Error en determinación: {e}")
        
        # Test 4: Preview de asiento contable
        print("\n=== Test 4: Preview de asiento contable ===")
        try:
            preview = account_service.get_journal_entry_lines_preview(test_invoice)
            
            total_debits = sum(line['debit_amount'] for line in preview)
            total_credits = sum(line['credit_amount'] for line in preview)
            
            print(f"✓ Preview generado - {len(preview)} líneas:")
            for line in preview:
                if line['debit_amount'] > 0:
                    print(f"  DÉBITO:  {line['account_code']} - {line['account_name']}: ${line['debit_amount']}")
                else:
                    print(f"  CRÉDITO: {line['account_code']} - {line['account_name']}: ${line['credit_amount']}")
            
            print(f"\nTotal débitos: ${total_debits}")
            print(f"Total créditos: ${total_credits}")
            print(f"Balanceado: {'✓' if total_debits == total_credits else '✗'}")
            
        except Exception as e:
            print(f"✗ Error en preview: {e}")
        
        print("\n✅ Test completado")
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_account_determination()
