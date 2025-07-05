#!/usr/bin/env python3
"""
Script para probar si la creación de pagos en estado borrador afecta cuentas contables
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

def test_draft_payment_impact():
    """
    Prueba si crear un pago en borrador afecta los saldos de las cuentas
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Probando impacto de pago borrador en cuentas ===")
        
        # 1. Obtener una cuenta bancaria
        bank_account = db.query(Account).filter(
            Account.code.like('1%'),  # Activos
            Account.is_active == True
        ).first()
        
        if not bank_account:
            print("No se encontró cuenta bancaria para la prueba")
            return
        
        print(f"Cuenta bancaria: {bank_account.code} - {bank_account.name}")
        print(f"Saldo inicial: {bank_account.balance}")
        
        # 2. Obtener un tercero (cliente o proveedor)
        third_party = db.query(ThirdParty).first()
        if not third_party:
            print("No se encontró tercero para la prueba")
            return
        
        print(f"Tercero: {third_party.name}")
        
        # 3. Obtener usuario
        user = db.query(User).first()
        if not user:
            print("No se encontró usuario para la prueba")
            return
        
        print(f"Usuario: {user.email}")
        
        # 4. Crear un pago en borrador
        print("\n--- Creando pago en borrador ---")
        
        payment = Payment(
            number=f"TEST-DRAFT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            reference="TEST-REFERENCE",
            payment_type=PaymentType.CUSTOMER_PAYMENT,
            payment_method=PaymentMethod.BANK_TRANSFER,
            status=PaymentStatus.DRAFT,
            third_party_id=third_party.id,
            payment_date=date.today(),
            value_date=date.today(),
            amount=Decimal('100.00'),
            allocated_amount=Decimal('0.00'),
            unallocated_amount=Decimal('100.00'),
            currency_code="COP",
            exchange_rate=Decimal('1'),
            account_id=bank_account.id,
            description="Pago de prueba en borrador",
            created_by_id=user.id
        )
        
        # Guardar y verificar saldos ANTES del commit
        db.add(payment)
        db.flush()  # Solo flush, no commit
        
        print(f"Pago creado: {payment.number} (ID: {payment.id})")
        print(f"Estado: {payment.status}")
        print(f"Monto: {payment.amount}")
        
        # 5. Verificar saldos después de crear el pago
        db.refresh(bank_account)  # Refrescar desde BD
        print(f"\nSaldo después de crear pago borrador: {bank_account.balance}")
        
        # 6. Verificar si hay asientos contables relacionados
        from app.models.journal_entry import JournalEntry
        journal_entries = db.query(JournalEntry).filter(
            JournalEntry.reference.like(f"%{payment.number}%")
        ).all()
        
        print(f"Asientos contables encontrados: {len(journal_entries)}")
        for entry in journal_entries:
            print(f"  - {entry.number}: {entry.description}")
        
        # 7. Verificar líneas de asiento que afecten la cuenta bancaria
        from app.models.journal_entry import JournalEntryLine
        account_lines = db.query(JournalEntryLine).filter(
            JournalEntryLine.account_id == bank_account.id
        ).order_by(JournalEntryLine.created_at.desc()).limit(5).all()
        
        print(f"\nÚltimas 5 líneas que afectaron la cuenta bancaria:")
        for line in account_lines:
            print(f"  - JE: {line.journal_entry.number if line.journal_entry else 'N/A'}")
            print(f"    Debe: {line.debit_amount}, Haber: {line.credit_amount}")
            print(f"    Referencia: {line.reference}")
            print(f"    Fecha: {line.created_at}")
            print()
        
        # 8. Verificar que el pago NO tenga journal_entry_id
        print(f"Payment journal_entry_id: {payment.journal_entry_id}")
        if payment.journal_entry_id:
            print("❌ ERROR: El pago borrador tiene asiento contable asignado")
        else:
            print("✓ Correcto: El pago borrador NO tiene asiento contable")
        
        print("\n=== Prueba completada ===")
        
        # No hacer commit para que no persista el pago de prueba
        db.rollback()
        
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_draft_payment_impact()
