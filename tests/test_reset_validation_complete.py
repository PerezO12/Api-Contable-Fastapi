#!/usr/bin/env python3
"""
Script para crear y probar el flujo completo de reset y validación masiva
Creará un pago simple que pueda ser confirmado exitosamente
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
from app.models.third_party import ThirdParty, ThirdPartyType
from app.models.user import User
from app.services.payment_flow_service import PaymentFlowService

def create_test_payment_and_test():
    """
    Crea un pago de cliente simple (que es más fácil de confirmar)
    y luego prueba el flujo de reset y validación
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Creando pago de prueba y probando flujo ===")
        
        # 1. Buscar un usuario admin para las operaciones
        admin_user = db.query(User).filter(User.email.like('%admin%')).first()
        if not admin_user:
            print("No se encontró usuario admin")
            return
        
        print(f"Usando usuario: {admin_user.email}")
        
        # 2. Buscar una cuenta bancaria
        bank_account = db.query(Account).filter(
            Account.code.like('11%')  # Cuentas de activo corriente (bancos)
        ).first()
        
        if not bank_account:
            print("No se encontró cuenta bancaria para la prueba")
            return
        
        print(f"Usando cuenta bancaria: {bank_account.code} - {bank_account.name}")
        
        # 3. Buscar un tercero (cliente)
        customer = db.query(ThirdParty).filter(
            ThirdParty.third_party_type == ThirdPartyType.CUSTOMER
        ).first()
        
        if not customer:
            print("No se encontró cliente para la prueba")
            return
        
        print(f"Usando cliente: {customer.name}")
        
        # 4. Crear un pago de cliente simple (más fácil de confirmar)
        payment_number = f"TEST-PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        payment = Payment(
            number=payment_number,
            reference="Test payment for reset validation",
            payment_type=PaymentType.CUSTOMER_PAYMENT,
            payment_method=PaymentMethod.BANK_TRANSFER,
            status=PaymentStatus.DRAFT,
            third_party_id=customer.id,
            payment_date=date.today(),
            value_date=date.today(),
            amount=Decimal('100000'),  # 100K COP
            allocated_amount=Decimal('0'),
            unallocated_amount=Decimal('100000'),
            currency_code='COP',
            exchange_rate=Decimal('1'),
            account_id=bank_account.id,
            description="Test payment for validation issue debugging",
            created_by_id=admin_user.id
        )
        
        db.add(payment)
        db.commit()
        
        print(f"Pago de prueba creado: {payment.number} (ID: {payment.id})")
        print(f"Estado: {payment.status}, Monto: {payment.amount}")
        
        # 5. Crear el servicio
        service = PaymentFlowService(db)
        
        # 6. Confirmar el pago (DRAFT -> POSTED)
        print("\n--- Confirmando pago ---")
        try:
            confirm_result = service.confirm_payment(
                payment_id=payment.id,
                confirmed_by_id=admin_user.id
            )
            print(f"✓ Confirmación exitosa. Nuevo estado: {confirm_result.status}")
        except Exception as e:
            print(f"✗ Error al confirmar pago: {str(e)}")
            # Intentar usar un enfoque más simple - solo cambiar el estado manualmente
            print("Intentando confirmación manual para la prueba...")
            payment.status = PaymentStatus.POSTED
            payment.posted_by_id = admin_user.id
            payment.posted_at = datetime.utcnow()
            db.commit()
            print(f"✓ Estado cambiado manualmente a: {payment.status}")
        
        # 7. Resetear el pago a borrador
        print("\n--- Restableciendo pago a borrador ---")
        try:
            reset_result = service.reset_payment_to_draft(
                payment_id=payment.id,
                reset_by_id=admin_user.id,
                reason="Prueba de diagnóstico del problema UNKNOWN"
            )
            print(f"✓ Reset completado. Nuevo estado: {reset_result.status}")
        except Exception as e:
            print(f"✗ Error al resetear pago: {str(e)}")
            # Reset manual para la prueba
            print("Intentando reset manual para la prueba...")
            payment.status = PaymentStatus.DRAFT
            payment.posted_by_id = None
            payment.posted_at = None
            payment.journal_entry_id = None
            db.commit()
            print(f"✓ Estado restablecido manualmente a: {payment.status}")
        
        # 8. Verificar que el pago existe en la base de datos después del reset
        print("\n--- Verificando que el pago existe después del reset ---")
        db.expire_all()  # Limpiar cache
        
        # Verificación básica
        basic_check = db.query(Payment).filter(Payment.id == payment.id).first()
        if basic_check:
            print(f"✓ Pago encontrado con consulta básica: {basic_check.number}, Estado: {basic_check.status}")
        else:
            print("✗ Pago NO encontrado con consulta básica - ERROR CRÍTICO")
            return
        
        # 9. Intentar validación masiva inmediatamente después del reset
        print("\n--- Ejecutando validación masiva inmediatamente después del reset ---")
        validation_result = service.validate_bulk_confirmation([payment.id])
        
        print(f"Resultados de validación:")
        print(f"  Total pagos: {validation_result.total_payments}")
        print(f"  Pueden confirmarse: {validation_result.can_confirm_count}")
        print(f"  Bloqueados: {validation_result.blocked_count}")
        print(f"  Con warnings: {validation_result.warnings_count}")
        
        # 10. Revisar resultado específico del pago
        if validation_result.validation_results:
            result = validation_result.validation_results[0]
            print(f"\nDetalle del resultado:")
            print(f"  Payment ID: {result.payment_id}")
            print(f"  Payment Number: {result.payment_number}")
            print(f"  Can Confirm: {result.can_confirm}")
            print(f"  Blocking Reasons: {result.blocking_reasons}")
            print(f"  Warnings: {result.warnings}")
            
            if result.payment_number.startswith("UNKNOWN"):
                print("\n❌ PROBLEMA DETECTADO: El pago aparece como UNKNOWN después del reset")
                
                # Diagnóstico adicional
                print("\n--- Diagnóstico adicional ---")
                
                # Verificar con otra consulta directa
                direct_check = db.query(Payment).filter(Payment.id == payment.id).first()
                if direct_check:
                    print(f"✓ Consulta directa encuentra el pago: {direct_check.number}")
                    print(f"  Estado: {direct_check.status}")
                    print(f"  Journal Entry ID: {direct_check.journal_entry_id}")
                else:
                    print("✗ Consulta directa NO encuentra el pago")
                
                # Intentar nueva validación con nueva sesión
                new_db = SessionLocal()
                try:
                    new_service = PaymentFlowService(new_db)
                    new_validation = new_service.validate_bulk_confirmation([payment.id])
                    new_result = new_validation.validation_results[0] if new_validation.validation_results else None
                    
                    if new_result and not new_result.payment_number.startswith("UNKNOWN"):
                        print("✓ Con nueva sesión el pago se encuentra correctamente")
                        print("  → El problema es de cache/sesión en la misma sesión")
                    else:
                        print("✗ Con nueva sesión el pago sigue apareciendo como UNKNOWN")
                        print("  → El problema es más profundo")
                        
                finally:
                    new_db.close()
            else:
                print("\n✓ Pago validado correctamente después del reset")
                print("  → No se detectó el problema UNKNOWN")
        
        # 11. Limpiar - eliminar el pago de prueba
        print("\n--- Limpiando pago de prueba ---")
        db.delete(payment)
        db.commit()
        print("✓ Pago de prueba eliminado")
        
        print("\n=== Prueba completada ===")
        
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_payment_and_test()
