#!/usr/bin/env python3
"""
Script para probar la corrección del error de enum en la confirmación de pagos
"""

import uuid
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.services.payment_flow_service import PaymentFlowService
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from sqlalchemy.orm import joinedload

def test_payment_confirmation():
    """Prueba la confirmación de un pago en borrador"""
    db = next(get_db())
    
    try:
        # Obtener el primer pago en estado DRAFT
        payment = db.query(Payment).filter(Payment.status == PaymentStatus.DRAFT).first()
        
        if not payment:
            print("❌ No se encontraron pagos en estado DRAFT")
            return False
            
        print(f"📋 Pago encontrado: {payment.number} (ID: {payment.id})")
        print(f"   Estado: {payment.status}")
        print(f"   Monto: ${payment.amount:,.2f}")
        print(f"   Tercero: {payment.third_party.name if payment.third_party else 'Sin tercero'}")
        print(f"   Diario ID: {payment.journal_id}")
        
        # Obtener un usuario admin para la confirmación
        admin_user = db.query(User).filter(User.is_active == True).first()
        if not admin_user:
            print("❌ No se encontró usuario activo")
            return False
            
        print(f"👤 Usuario confirmante: {admin_user.email}")
        
        # Crear servicio y confirmar pago
        flow_service = PaymentFlowService(db)
        
        print("\n🔄 Confirmando pago...")
        confirmed_payment = flow_service.confirm_payment(payment.id, admin_user.id)
        
        print("✅ ¡Pago confirmado exitosamente!")
        print(f"   Estado final: {confirmed_payment.status}")
        
        # Obtener el pago actualizado de la base de datos para mostrar más detalles
        updated_payment = db.query(Payment).filter(Payment.id == payment.id).first()
        if updated_payment:
            print(f"   Asiento contable ID: {getattr(updated_payment, 'journal_entry_id', 'N/A')}")
            print(f"   Fecha de confirmación: {getattr(updated_payment, 'posted_at', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al confirmar pago: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Probando corrección del error de enum en confirmación de pagos\n")
    success = test_payment_confirmation()
    
    if success:
        print("\n🎉 Prueba exitosa - El error del enum ha sido corregido!")
    else:
        print("\n💥 Prueba fallida - El error persiste o hay otros problemas")
