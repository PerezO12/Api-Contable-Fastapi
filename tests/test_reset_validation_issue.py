#!/usr/bin/env python3
"""
Script para reproducir y diagnosticar el problema con pagos restablecid        # 6. Verificar que el pago existe en la base de datos después del reset
        print("\n--- Verificando que el pago existe después del reset ---")
        db.expire_all()  # Limpiar cache
        
        # Verificación básica
        basic_check = db.query(Payment).filter(Payment.id == draft_payment.id).first()
        if basic_check:
            print(f"✓ Pago encontrado con consulta básica: {basic_check.number}, Estado: {basic_check.status}")
        else:
            print("✗ Pago NO encontrado con consulta básica - ERROR CRÍTICO")
            return
        
        # 7. Intentar validación masiva inmediatamente después del reset
        print("\n--- Ejecutando validación masiva inmediatamente después del reset ---")
        validation_result = service.validate_bulk_confirmation([draft_payment.id])que aparecen como "UNKNOWN" en la validación masiva.
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
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.payment_flow_service import PaymentFlowService

def test_reset_validation_issue():
    """
    Prueba el escenario completo:
    1. Crear un pago
    2. Confirmarlo (POSTED)
    3. Restablecerlo a borrador (DRAFT)
    4. Validar inmediatamente después del reset
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== Iniciando prueba de reset y validación ===")
        
        # 1. Buscar un usuario admin para las operaciones
        admin_user = db.query(User).filter(User.email.like('%admin%')).first()
        if not admin_user:
            print("No se encontró usuario admin, creando uno temporal...")
            # Crear usuario temporal para la prueba
            admin_user = User(
                email="test_admin@test.com",
                first_name="Test",
                last_name="Admin",
                hashed_password="dummy",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Usuario admin creado: {admin_user.email}")
        
        print(f"Usando usuario: {admin_user.email}")
        
        # 2. Buscar un pago existente en estado DRAFT que podamos confirmar
        draft_payment = db.query(Payment).filter(
            Payment.status == PaymentStatus.DRAFT
        ).first()
        
        if not draft_payment:
            print("No se encontró ningún pago en estado DRAFT para la prueba")
            return
        
        print(f"Pago encontrado para prueba: {draft_payment.number} (ID: {draft_payment.id})")
        print(f"Estado inicial: {draft_payment.status}")
        print(f"Monto: {draft_payment.amount}")
        
        # 3. Crear el servicio
        service = PaymentFlowService(db)
        
        # 4. Confirmar el pago primero (DRAFT -> POSTED)
        print("\n--- Confirmando pago ---")
        try:
            confirm_result = service.confirm_payment(
                payment_id=draft_payment.id,
                confirmed_by_id=admin_user.id
            )
            print(f"Confirmación completada. Nuevo estado: {confirm_result.status}")
        except Exception as e:
            print(f"Error al confirmar pago: {str(e)}")
            # Si no puede confirmar, buscar uno ya confirmado
            posted_payment = db.query(Payment).filter(
                Payment.status == PaymentStatus.POSTED
            ).first()
            if posted_payment:
                draft_payment = posted_payment
                print(f"Usando pago ya confirmado: {draft_payment.number}")
            else:
                print("No hay pagos confirmados disponibles para la prueba")
                return
        
        # 5. Resetear el pago a borrador
        print("\n--- Restableciendo pago a borrador ---")
        reset_result = service.reset_payment_to_draft(
            payment_id=draft_payment.id,
            reset_by_id=admin_user.id,
            reason="Prueba de diagnóstico del problema UNKNOWN"
        )
        
        print(f"Reset completado. Nuevo estado: {reset_result.status}")
        
        # 6. Verificar que el pago existe en la base de datos después del reset
        print("\n--- Verificando que el pago existe después del reset ---")
        db.expire_all()  # Limpiar cache
        
        # Verificación básica
        basic_check = db.query(Payment).filter(Payment.id == posted_payment.id).first()
        if basic_check:
            print(f"✓ Pago encontrado con consulta básica: {basic_check.number}, Estado: {basic_check.status}")
        else:
            print("✗ Pago NO encontrado con consulta básica - ERROR CRÍTICO")
            return
        
        # 6. Intentar validación masiva inmediatamente después del reset
        print("\n--- Ejecutando validación masiva inmediatamente después del reset ---")
        validation_result = service.validate_bulk_confirmation([posted_payment.id])
        
        print(f"Resultados de validación:")
        print(f"  Total pagos: {validation_result.total_payments}")
        print(f"  Pueden confirmarse: {validation_result.can_confirm_count}")
        print(f"  Bloqueados: {validation_result.blocked_count}")
        print(f"  Con warnings: {validation_result.warnings_count}")
        
        # 7. Revisar resultado específico del pago
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
                
                # Intentar nueva validación con nueva sesión
                new_db = SessionLocal()
                try:
                    new_service = PaymentFlowService(new_db)
                    new_validation = new_service.validate_bulk_confirmation([draft_payment.id])
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
        
        print("\n=== Prueba completada ===")
        
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_reset_validation_issue()
