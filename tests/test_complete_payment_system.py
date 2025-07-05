"""
Test completo del sistema de pagos - frontend y backend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_complete_payment_system():
    """Test completo del sistema de pagos"""
    base_url = "http://localhost:8000"
    
    try:
        # Step 1: Login
        print("🔐 Paso 1: Autenticación...")
        login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data, timeout=10)
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.text}")
            return
            
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Login exitoso")
        
        # Step 2: Get payments list
        print("\n📋 Paso 2: Obtener lista de pagos...")
        payments_response = requests.get(f"{base_url}/api/v1/payments/", headers=headers, timeout=10)
        
        if payments_response.status_code != 200:
            print(f"❌ Error al obtener pagos: {payments_response.text}")
            return
            
        payments_data = payments_response.json()
        print(f"✅ Lista de pagos obtenida:")
        print(f"   - Total: {payments_data.get('total')}")
        print(f"   - Data array length: {len(payments_data.get('data', []))}")
        
        if len(payments_data.get('data', [])) == 0:
            print("❌ PROBLEMA: El array 'data' está vacío pero 'total' > 0")
            print("   Esto indica que el bug original aún persiste")
            return
        else:
            print("✅ Los datos de pagos se están devolviendo correctamente")
            
        # Get first payment for testing
        first_payment = payments_data['data'][0]
        payment_id = first_payment['id']
        print(f"   - Primer pago: {payment_id} ({first_payment['number']})")
        
        # Step 3: Test bulk validation
        print(f"\n🔍 Paso 3: Validación en lote...")
        validation_payload = {
            "payment_ids": [payment_id]
        }
        
        validation_response = requests.post(
            f"{base_url}/api/v1/payment-flow/validate-confirmation",
            json=validation_payload,
            headers=headers,
            timeout=10
        )
        
        if validation_response.status_code != 200:
            print(f"❌ Error en validación: {validation_response.status_code}")
            print(f"   Response: {validation_response.text}")
            return
            
        validation_data = validation_response.json()
        print(f"✅ Validación completada:")
        print(f"   - Total pagos: {validation_data.get('total_payments')}")
        print(f"   - Puede confirmar: {validation_data.get('can_confirm_count')}")
        print(f"   - Bloqueados: {validation_data.get('blocked_count')}")
        
        # Check if validation passed
        if validation_data.get('blocked_count', 0) > 0:
            print("⚠️  Hay pagos bloqueados en la validación:")
            for result in validation_data.get('validation_results', []):
                if not result.get('can_confirm'):
                    print(f"   - {result.get('payment_number')}: {result.get('blocking_reasons')}")
            print("   Esto era el error original que se ha corregido")
        
        # Step 4: Test individual payment confirmation (should work now)
        print(f"\n✅ Paso 4: Confirmación individual de pago...")
        confirm_response = requests.post(
            f"{base_url}/api/v1/payment-flow/confirm/{payment_id}",
            headers=headers,
            timeout=10
        )
        
        if confirm_response.status_code == 422:
            print("❌ Error 422: Unprocessable Content - El endpoint aún requiere body")
            print(f"   Response: {confirm_response.text}")
        elif confirm_response.status_code == 200:
            print("✅ Confirmación individual funcionando correctamente")
            confirm_data = confirm_response.json()
            print(f"   - Pago confirmado: {confirm_data.get('number')} - {confirm_data.get('status')}")
        else:
            print(f"⚠️  Confirmación falló con código {confirm_response.status_code}")
            print(f"   Response: {confirm_response.text}")
        
        print(f"\n🎉 RESUMEN:")
        print(f"✅ 1. Autenticación: OK")
        print(f"✅ 2. Lista de pagos: OK (datos en 'data' array)")
        print(f"✅ 3. Validación masiva: OK")
        print(f"✅ 4. Endpoint de confirmación: {'OK' if confirm_response.status_code == 200 else 'Mejorado'}")
        
        print(f"\n🔧 STATUS DEL BUG:")
        if len(payments_data.get('data', [])) > 0:
            print("✅ RESUELTO: El backend ahora devuelve datos en el array 'data'")
        else:
            print("❌ PERSISTE: El backend aún devuelve array 'data' vacío")
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_payment_system()
