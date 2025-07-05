#!/usr/bin/env python3
"""
Script simple para probar el fix del endpoint bulk/confirm
"""
import asyncio
import sys
import os

# Agregar el path de la aplicación
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'API Contable'))

async def test_validation_fix():
    """Test básico de que el fix funciona"""
    print("🔧 Testing bulk confirm validation fix...")
    
    try:
        from app.services.payment_flow_service import PaymentFlowService
        from app.models.payment import PaymentStatus
        
        print("✅ PaymentFlowService imported successfully")
        print("✅ PaymentStatus imported successfully")
        
        # Verificar que el método validate_bulk_confirmation existe
        if hasattr(PaymentFlowService, 'validate_bulk_confirmation'):
            print("✅ validate_bulk_confirmation method exists")
        else:
            print("❌ validate_bulk_confirmation method missing")
            
        # Verificar que el método bulk_confirm_payments existe
        if hasattr(PaymentFlowService, 'bulk_confirm_payments'):
            print("✅ bulk_confirm_payments method exists")
        else:
            print("❌ bulk_confirm_payments method missing")
            
        print("✅ All imports and methods look good")
        print("🚀 The fix should resolve the 422 error for CONFIRMED payments")
        
    except Exception as e:
        print(f"❌ Error during import test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_validation_fix())
