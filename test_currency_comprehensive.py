#!/usr/bin/env python3
"""
Comprehensive integration test for currency change functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_currency_change_comprehensive():
    print("🚀 Test comprensivo de cambio de moneda")
    print("=" * 50)
    
    # Authenticate
    print("🔐 Autenticándose...")
    login_data = {
        "email": "admin@contable.com", 
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    assert response.status_code == 200, f"Auth failed: {response.status_code}"
    
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ Autenticación exitosa")
    
    test_cases = [
        {"from": "EUR", "to": "USD", "should_succeed": True},
        {"from": "USD", "to": "CAD", "should_succeed": True},
        {"from": "CAD", "to": "GBP", "should_succeed": True},
        {"from": "GBP", "to": "JPY", "should_succeed": True},
        {"from": "JPY", "to": "EUR", "should_succeed": True},
    ]
    
    success_count = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: Cambio de {case['from']} a {case['to']}")
        
        # Perform currency change
        change_data = {"currency_code": case['to']}
        response = requests.put(
            f"{BASE_URL}/api/v1/company-settings/",
            json=change_data,
            headers=headers
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if case['should_succeed']:
            if response.status_code == 200:
                print("✅ Cambio exitoso")
                
                # Verify the change
                response = requests.get(f"{BASE_URL}/api/v1/company-settings/", headers=headers)
                if response.status_code == 200:
                    settings = response.json()
                    actual_currency = settings.get("currency_code")
                    if actual_currency == case['to']:
                        print(f"✅ Verificado: Moneda = {actual_currency}")
                        success_count += 1
                    else:
                        print(f"❌ Error verificación: Esperado {case['to']}, Actual {actual_currency}")
                else:
                    print(f"❌ Error verificando configuración: {response.status_code}")
            else:
                print(f"❌ Error en cambio: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            if response.status_code != 200:
                print("✅ Error esperado")
                success_count += 1
            else:
                print("❌ Debería haber fallado pero tuvo éxito")
    
    print(f"\n🏆 Resultados: {success_count}/{len(test_cases)} pruebas exitosas")
    
    if success_count == len(test_cases):
        print("🎉 ¡Todos los tests de cambio de moneda PASARON!")
        print("✅ El bug del error 500 ha sido CORREGIDO")
        return True
    else:
        print("❌ Algunos tests fallaron")
        return False

if __name__ == "__main__":
    success = test_currency_change_comprehensive()
    exit(0 if success else 1)
