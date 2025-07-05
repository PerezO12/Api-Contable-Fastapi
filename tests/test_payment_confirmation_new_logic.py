#!/usr/bin/env python3
"""
Script para probar el flujo completo de confirmación de pagos
con la nueva lógica de cuentas contables desde el journal.
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
from app.models.user import User
from app.services.payment_flow_service import PaymentFlowService

def test_payment_confirmation_with_journal_config():
    """
    Prueba el flujo completo de confirmación de pagos usando
    la nueva lógica de cuentas contables desde el journal.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Iniciando prueba de confirmación con configuración de journal ===")
        
        # 1. Buscar un usuario admin
        admin_user = db.query(User).filter(User.email.like('%admin%')).first()
        if not admin_user:
            print("No se encontró usuario admin")
            return
        
        print(f"Usando usuario: {admin_user.email}")
        
        # 2. Buscar un pago de proveedor sin facturas asignadas
        supplier_payment = db.query(Payment).filter(
            Payment.status == PaymentStatus.DRAFT,
            Payment.payment_type == PaymentType.SUPPLIER_PAYMENT
        ).first()
        
        if not supplier_payment:
            print("No se encontró pago de proveedor en borrador")
            return
        
        print(f"Pago encontrado: {supplier_payment.number}")
        print(f"  - Tipo: {supplier_payment.payment_type}")
        print(f"  - Monto: {supplier_payment.amount}")
        print(f"  - Facturas asignadas: {len(supplier_payment.payment_invoices)}")
        
        # 3. Crear el servicio
        service = PaymentFlowService(db)
        
        # 4. Intentar validación antes de confirmar
        print("\n--- Validando pago para confirmación ---")
        try:
            validation_result = service.validate_bulk_confirmation([supplier_payment.id])
            
            if validation_result.validation_results:
                result = validation_result.validation_results[0]
                print(f"Resultado de validación:")
                print(f"  - Payment Number: {result.payment_number}")
                print(f"  - Can Confirm: {result.can_confirm}")
                print(f"  - Blocking Reasons: {result.blocking_reasons}")
                print(f"  - Warnings: {result.warnings}")
                
                if not result.can_confirm:
                    print("⚠ El pago no puede confirmarse debido a errores de validación")
                    return
            else:
                print("⚠ No se obtuvo resultado de validación")
                return
                
        except Exception as e:
            print(f"✗ Error en validación: {str(e)}")
            return
        
        # 5. Intentar confirmar el pago
        print("\n--- Intentando confirmar el pago ---")
        try:
            confirmed_payment_response = service.confirm_payment(
                payment_id=supplier_payment.id,
                confirmed_by_id=admin_user.id
            )
            
            print(f"✓ Pago confirmado exitosamente")
            print(f"  - Nuevo estado: {confirmed_payment_response.status}")
            
            # Recargar el pago desde la base de datos para obtener el journal_entry_id
            db.refresh(supplier_payment)
            
            print(f"  - Journal Entry ID: {supplier_payment.journal_entry_id}")
            
            # 6. Verificar las líneas del asiento contable
            if supplier_payment.journal_entry_id:
                from app.models.journal_entry import JournalEntry, JournalEntryLine
                journal_entry = db.query(JournalEntry).filter(
                    JournalEntry.id == supplier_payment.journal_entry_id
                ).first()
                
                if journal_entry:
                    print(f"\n--- Detalle del asiento contable ---")
                    print(f"Asiento: {journal_entry.number}")
                    if journal_entry.journal:
                        print(f"Journal: {journal_entry.journal.name}")
                    
                    lines = db.query(JournalEntryLine).filter(
                        JournalEntryLine.journal_entry_id == journal_entry.id
                    ).all()
                    
                    for line in lines:
                        print(f"  Línea {line.line_number}:")
                        print(f"    - Cuenta: {line.account.code} - {line.account.name}")
                        print(f"    - Debe: {line.debit_amount or 0}")
                        print(f"    - Haber: {line.credit_amount or 0}")
                        print(f"    - Descripción: {line.description}")
            
            print("\n✓ Confirmación exitosa con nueva lógica de cuentas contables")
            
        except Exception as e:
            print(f"✗ Error al confirmar pago: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== Prueba completada ===")
        
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_payment_confirmation_with_journal_config()
