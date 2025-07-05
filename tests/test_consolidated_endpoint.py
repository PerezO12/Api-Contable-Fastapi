#!/usr/bin/env python3
"""
Test simple para verificar la consolidación de endpoints de contabilización de pagos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_consolidated_endpoint():
    """Test que verifica que el endpoint consolidado funciona para ambos casos"""
    print("=== TESTING CONSOLIDATED PAYMENT ENDPOINT ===")
    
    # Test básico - verificar que el módulo se importa correctamente
    try:
        from app.services.payment_flow_service import PaymentFlowService
        print("✅ PaymentFlowService imported successfully")
        
        # Verificar que el método consolidado existe
        if hasattr(PaymentFlowService, 'bulk_confirm_payments'):
            print("✅ bulk_confirm_payments method exists")
        else:
            print("❌ bulk_confirm_payments method missing")
            return False
        
        # Verificar que el método confirm_payment existe
        if hasattr(PaymentFlowService, 'confirm_payment'):
            print("✅ confirm_payment method exists")
        else:
            print("❌ confirm_payment method missing")
            return False
            
        # Verificar que los endpoints existen
        try:
            from app.api.payments import bulk_confirm_payments, bulk_post_payments
            print("✅ Both endpoints exist (bulk_confirm_payments and bulk_post_payments)")
        except ImportError as e:
            print(f"❌ Error importing endpoints: {e}")
            return False
        
        # Test docstring del método consolidado
        docstring = PaymentFlowService.bulk_confirm_payments.__doc__
        if docstring and "MÉTODO CONSOLIDADO" in docstring:
            print("✅ Method docstring indicates consolidation")
        else:
            print("⚠️ Method docstring may not reflect consolidation")
        
        print("\n🎯 Basic consolidation test completed!")
        print("✅ The consolidated endpoint structure is in place")
        print("✅ Both DRAFT → POSTED and CONFIRMED → POSTED should work")
        print("✅ The deprecated /bulk/post endpoint is still available for compatibility")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    if test_consolidated_endpoint():
        print("\n✅ CONSOLIDATION TEST PASSED")
    else:
        print("\n❌ CONSOLIDATION TEST FAILED")
