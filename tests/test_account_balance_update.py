#!/usr/bin/env python3
"""
Script para diagnosticar el problema de actualización de saldos de cuentas
cuando se confirma un pago.
"""

import sys
import os
import uuid
from decimal import Decimal
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod
from app.models.account import Account
from app.models.third_party import ThirdParty
from app.models.user import User
from app.models.journal_entry import JournalEntry, JournalEntryLine
from app.services.payment_flow_service import PaymentFlowService

def test_account_balance_update():
    """
    Prueba específica para verificar si los saldos de cuentas se actualizan
    correctamente al confirmar un pago.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Diagnosticando actualización de saldos de cuentas ===")
        
        # 1. Buscar un pago en estado DRAFT
        draft_payment = db.query(Payment).filter(
            Payment.status == PaymentStatus.DRAFT
        ).first()
        
        if not draft_payment:
            print("No se encontró pago en borrador para la prueba")
            return
        
        print(f"Pago encontrado: {draft_payment.number}")
        print(f"Tipo: {draft_payment.payment_type}")
        print(f"Monto: {draft_payment.amount}")
        
        # 2. Obtener la cuenta asociada al pago
        bank_account = db.query(Account).filter(Account.id == draft_payment.account_id).first()
        if not bank_account:
            print("No se encontró la cuenta bancaria del pago")
            return
        
        print(f"\nCuenta bancaria: {bank_account.code} - {bank_account.name}")
        print(f"Saldo inicial: {bank_account.balance}")
        print(f"Saldo débito inicial: {bank_account.debit_balance}")
        print(f"Saldo crédito inicial: {bank_account.credit_balance}")
        
        # 3. Buscar cuentas que podrían ser afectadas por el pago
        print("\n--- Identificando cuentas que podrían ser afectadas ---")
        
        # Para pagos de cliente: cuenta bancaria (debe) + cuenta por cobrar o ingresos (haber)
        # Para pagos de proveedor: cuenta por pagar o gastos (debe) + cuenta bancaria (haber)
        
        service = PaymentFlowService(db)
        
        if draft_payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
            print("Pago de cliente - buscando cuenta de ingresos...")
            try:
                # Obtener journal del pago para obtener cuenta de ingresos
                journal_id = draft_payment.journal_id
                if not journal_id:
                    journal_id = service._determine_payment_journal(draft_payment)
                
                journal = db.query(Journal).filter(Journal.id == journal_id).first()
                if journal:
                    income_account = service._get_unallocated_income_account_from_journal(journal)
                    print(f"Cuenta de ingresos: {income_account.code} - {income_account.name}")
                    print(f"Saldo inicial ingresos: {income_account.balance}")
                    
            except Exception as e:
                print(f"Error obteniendo cuenta de ingresos: {str(e)}")
                
        elif draft_payment.payment_type == PaymentType.SUPPLIER_PAYMENT:
            print("Pago de proveedor - buscando cuenta de gastos...")
            try:
                # Obtener journal del pago para obtener cuenta de gastos
                journal_id = draft_payment.journal_id
                if not journal_id:
                    journal_id = service._determine_payment_journal(draft_payment)
                
                journal = db.query(Journal).filter(Journal.id == journal_id).first()
                if journal:
                    expense_account = service._get_unallocated_expense_account_from_journal(journal)
                    print(f"Cuenta de gastos: {expense_account.code} - {expense_account.name}")
                    print(f"Saldo inicial gastos: {expense_account.balance}")
                    
            except Exception as e:
                print(f"Error obteniendo cuenta de gastos: {str(e)}")
        
        # 4. Buscar usuario admin
        admin_user = db.query(User).filter(User.email.like('%admin%')).first()
        if not admin_user:
            print("No se encontró usuario admin")
            return
        
        # 5. Confirmar el pago y verificar los cambios
        print(f"\n--- Confirmando pago ---")
        try:
            confirm_result = service.confirm_payment(
                payment_id=draft_payment.id,
                confirmed_by_id=admin_user.id
            )
            
            print(f"✓ Pago confirmado: {confirm_result.status}")
            
            # Refrescar el pago desde la BD
            db.refresh(draft_payment)
            print(f"Journal Entry ID: {draft_payment.journal_entry_id}")
            
        except Exception as e:
            print(f"✗ Error confirmando pago: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # 6. Verificar el asiento contable creado
        if draft_payment.journal_entry_id:
            journal_entry = db.query(JournalEntry).filter(
                JournalEntry.id == draft_payment.journal_entry_id
            ).first()
            
            if journal_entry:
                print(f"\n--- Asiento contable creado ---")
                print(f"Número: {journal_entry.number}")
                print(f"Debe total: {journal_entry.total_debit}")
                print(f"Haber total: {journal_entry.total_credit}")
                
                # Verificar líneas del asiento
                lines = db.query(JournalEntryLine).filter(
                    JournalEntryLine.journal_entry_id == journal_entry.id
                ).all()
                
                print(f"\n--- Líneas del asiento ---")
                for line in lines:
                    print(f"Línea {line.line_number}:")
                    print(f"  Cuenta: {line.account.code} - {line.account.name}")
                    print(f"  Debe: {line.debit_amount or 0}")
                    print(f"  Haber: {line.credit_amount or 0}")
                    print(f"  Descripción: {line.description}")
                    print()
            else:
                print("⚠ No se encontró el asiento contable")
        else:
            print("⚠ El pago no tiene asiento contable asignado")
        
        # 7. Verificar saldos DESPUÉS de la confirmación
        print("--- Verificando saldos después de confirmación ---")
        
        # Refrescar cuenta bancaria
        db.refresh(bank_account)
        print(f"Cuenta bancaria después: {bank_account.code} - {bank_account.name}")
        print(f"Saldo final: {bank_account.balance}")
        print(f"Saldo débito final: {bank_account.debit_balance}")
        print(f"Saldo crédito final: {bank_account.credit_balance}")
        
        # Verificar si hubo cambios
        balance_change = bank_account.balance - bank_account.balance  # Esto necesita ser calculado correctamente
        print(f"Cambio en saldo: (necesita cálculo correcto)")
        
        # 8. Verificar que las líneas del asiento realmente existan en BD
        if draft_payment.journal_entry_id:
            lines_count = db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == draft_payment.journal_entry_id
            ).count()
            print(f"\nLíneas de asiento en BD: {lines_count}")
            
            # Verificar líneas que afecten específicamente la cuenta bancaria
            bank_lines = db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == draft_payment.journal_entry_id,
                JournalEntryLine.account_id == bank_account.id
            ).all()
            
            print(f"Líneas que afectan cuenta bancaria: {len(bank_lines)}")
            for line in bank_lines:
                print(f"  Debe: {line.debit_amount}, Haber: {line.credit_amount}")
        
        print("\n=== Diagnóstico completado ===")
        
    except Exception as e:
        print(f"Error durante diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_account_balance_update()
