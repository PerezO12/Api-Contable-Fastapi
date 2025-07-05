#!/usr/bin/env python3
"""
Script para probar la nueva lógica de obtención de cuentas contables
desde la configuración del journal bancario.
"""

import sys
import os
import uuid
from decimal import Decimal
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.models.journal import Journal, JournalType
from app.models.bank_journal_config import BankJournalConfig
from app.models.account import Account
from app.models.user import User
from app.models.third_party import ThirdParty
from app.services.payment_flow_service import PaymentFlowService

def test_journal_configuration():
    """
    Prueba la nueva funcionalidad de configuración de cuentas contables
    basada en el journal asignado al pago.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Iniciando prueba de configuración de journal ===")
        
        # 1. Buscar un usuario admin
        admin_user = db.query(User).filter(User.email.like('%admin%')).first()
        if not admin_user:
            print("No se encontró usuario admin")
            return
        
        print(f"Usando usuario: {admin_user.email}")
        
        # 2. Buscar un journal de tipo BANK
        bank_journal = db.query(Journal).filter(
            Journal.type == JournalType.BANK,
            Journal.is_active == True
        ).first()
        
        if not bank_journal:
            print("No se encontró journal bancario para la prueba")
            return
        
        print(f"Journal bancario encontrado: {bank_journal.name} ({bank_journal.code})")
        
        # 3. Verificar si tiene configuración bancaria
        bank_config = bank_journal.get_bank_config()
        if bank_config:
            print("✓ Journal tiene configuración bancaria")
            print(f"  - Cuenta bancaria: {bank_config.bank_account.name if bank_config.bank_account else 'No configurada'}")
            print(f"  - Cuenta de recibo: {bank_config.inbound_receipt_account.name if bank_config.inbound_receipt_account else 'No configurada'}")
            print(f"  - Cuenta pendientes salida: {bank_config.outbound_pending_account.name if bank_config.outbound_pending_account else 'No configurada'}")
            print(f"  - Cuenta ganancias: {bank_config.profit_account.name if bank_config.profit_account else 'No configurada'}")
            print(f"  - Cuenta pérdidas: {bank_config.loss_account.name if bank_config.loss_account else 'No configurada'}")
        else:
            print("⚠ Journal no tiene configuración bancaria")
        
        # 4. Crear el servicio para probar las nuevas funciones
        service = PaymentFlowService(db)
        
        # 5. Probar obtención de cuentas de ingresos desde journal
        print("\n--- Probando obtención de cuenta de ingresos ---")
        try:
            income_account = service._get_unallocated_income_account_from_journal(bank_journal)
            print(f"✓ Cuenta de ingresos obtenida: {income_account.code} - {income_account.name}")
        except Exception as e:
            print(f"✗ Error obteniendo cuenta de ingresos: {str(e)}")
        
        # 6. Probar obtención de cuentas de gastos desde journal
        print("\n--- Probando obtención de cuenta de gastos ---")
        try:
            expense_account = service._get_unallocated_expense_account_from_journal(bank_journal)
            print(f"✓ Cuenta de gastos obtenida: {expense_account.code} - {expense_account.name}")
        except Exception as e:
            print(f"✗ Error obteniendo cuenta de gastos: {str(e)}")
        
        # 7. Probar validación de configuración de journal
        print("\n--- Probando validación de configuración de journal ---")
        
        # Buscar un pago de prueba
        test_payment = db.query(Payment).filter(
            Payment.status == PaymentStatus.DRAFT,
            Payment.payment_type == PaymentType.SUPPLIER_PAYMENT
        ).first()
        
        if test_payment:
            print(f"Pago de prueba encontrado: {test_payment.number}")
            validation_errors = service._validate_journal_configuration_for_payment(test_payment, bank_journal)
            
            if validation_errors:
                print("⚠ Errores de validación encontrados:")
                for error in validation_errors:
                    print(f"  - {error}")
            else:
                print("✓ Journal configurado correctamente para pagos")
        else:
            print("No se encontró pago de prueba")
        
        # 8. Verificar las cuentas por defecto vs configuración bancaria
        print("\n--- Comparando métodos de obtención de cuentas ---")
        
        # Método antiguo (fallback)
        try:
            old_income = service._get_unallocated_income_account_fallback()
            print(f"Método fallback - Cuenta ingresos: {old_income.code} - {old_income.name}")
        except Exception as e:
            print(f"Método fallback - Error ingresos: {str(e)}")
        
        try:
            old_expense = service._get_unallocated_expense_account_fallback()
            print(f"Método fallback - Cuenta gastos: {old_expense.code} - {old_expense.name}")
        except Exception as e:
            print(f"Método fallback - Error gastos: {str(e)}")
        
        # Método nuevo (desde journal)
        try:
            new_income = service._get_unallocated_income_account_from_journal(bank_journal)
            print(f"Método journal - Cuenta ingresos: {new_income.code} - {new_income.name}")
        except Exception as e:
            print(f"Método journal - Error ingresos: {str(e)}")
        
        try:
            new_expense = service._get_unallocated_expense_account_from_journal(bank_journal)
            print(f"Método journal - Cuenta gastos: {new_expense.code} - {new_expense.name}")
        except Exception as e:
            print(f"Método journal - Error gastos: {str(e)}")
        
        print("\n=== Prueba completada ===")
        
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_journal_configuration()
