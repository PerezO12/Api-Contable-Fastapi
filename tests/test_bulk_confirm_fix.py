#!/usr/bin/env python3
"""
Script para probar el fix del endpoint bulk/confirm
"""
import asyncio
import sys
import os

# Agregar el path de la aplicación
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API Contable'))

from app.database import get_async_db
from app.services.payment_flow_service import PaymentFlowService
from app.models.payment import Payment, PaymentStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def test_bulk_confirm_fix():
    """Test que el bulk confirm funciona correctamente"""
    
    print("🔧 Testing bulk confirm fix...")
    
    # Obtener conexión a la BD
    async for db in get_async_db():
        try:
            # Buscar algunos pagos DRAFT
            draft_payments_result = await db.execute(
                select(Payment).where(Payment.status == PaymentStatus.DRAFT).limit(5)
            )
            draft_payments = draft_payments_result.scalars().all()
            
            if not draft_payments:
                print("❌ No hay pagos DRAFT para probar")
                return
            
            payment_ids = [p.id for p in draft_payments]
            print(f"📋 Found {len(payment_ids)} DRAFT payments to test")
            
            # Crear servicio
            service = PaymentFlowService(db)
            
            # Probar validación
            print("🔍 Testing validation...")
            validation_result = await service.validate_bulk_confirmation(payment_ids)
            
            print(f"✅ Validation completed:")
            print(f"  - Total payments: {validation_result['total_payments']}")
            print(f"  - Valid: {validation_result['summary']['valid']}")
            print(f"  - Invalid: {validation_result['summary']['invalid']}")
            print(f"  - Warnings: {validation_result['summary']['warnings']}")
            
            # Mostrar detalles si hay errores
            if validation_result['summary']['invalid'] > 0:
                print("❌ Validation errors found:")
                for payment_id, result in validation_result['validation_results'].items():
                    if not result['valid']:
                        print(f"  - Payment {result.get('payment_number', payment_id)}: {result['errors']}")
            
            # Si hay pagos válidos, probar bulk confirm
            if validation_result['summary']['valid'] > 0:
                print("🚀 Testing bulk confirm with valid payments...")
                
                # Obtener solo los pagos válidos
                valid_payment_ids = [
                    payment_id for payment_id, result in validation_result['validation_results'].items()
                    if result['valid']
                ]
                
                # Crear un usuario dummy para la prueba
                dummy_user_id = draft_payments[0].created_by_id or payment_ids[0]
                
                try:
                    confirm_result = await service.bulk_confirm_payments(
                        [uuid.UUID(pid) for pid in valid_payment_ids[:1]],  # Solo probar con 1 pago
                        dummy_user_id,
                        confirmation_notes="Test bulk confirm fix"
                    )
                    
                    print(f"✅ Bulk confirm completed:")
                    print(f"  - Successful: {confirm_result['successful']}")
                    print(f"  - Failed: {confirm_result['failed']}")
                    
                except Exception as e:
                    print(f"❌ Bulk confirm failed: {e}")
                    
            else:
                print("⚠️ No valid payments to test bulk confirm")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    import uuid
    asyncio.run(test_bulk_confirm_fix())
