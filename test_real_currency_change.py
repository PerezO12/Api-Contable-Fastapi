#!/usr/bin/env python3
"""
Test real currency change between different currencies
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_currency_change():
    print("🚀 Test de cambio de moneda real entre diferentes monedas")
    print("=" * 60)
    
    # 0. Authenticate
    print("0️⃣ Autenticándose...")
    login_data = {
        "email": "admin@contable.com",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Error en autenticación: {response.status_code}")
        print(response.text)
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ Autenticación exitosa")
    
    # 1. Get current configuration
    print("\n1️⃣ Obteniendo configuración actual...")
    response = requests.get(f"{BASE_URL}/api/v1/company-settings/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo configuración: {response.status_code}")
        print(response.text)
        return
    
    settings = response.json()
    current_currency = settings.get("currency_code", "USD")
    print(f"✅ Moneda actual: {current_currency}")
    
    # 2. Make sure we have multiple active currencies
    print("\n2️⃣ Verificando monedas disponibles...")
    response = requests.get(f"{BASE_URL}/api/v1/currencies", headers=headers)
    
    if response.status_code == 200:
        currencies_data = response.json()
        currencies = currencies_data.get('currencies', [])
        active_currencies = [c for c in currencies if c.get('is_active')]
        print(f"✅ Monedas activas: {len(active_currencies)}")
        
        # Print available currencies
        for currency in active_currencies:
            print(f"   - {currency.get('code')}: {currency.get('name')}")
    
    # 3. Test currency change from current to a different one
    target_currencies = ["USD", "EUR", "COP"]
    
    for target_currency in target_currencies:
        if target_currency != current_currency:
            print(f"\n3️⃣ Probando cambio de {current_currency} a {target_currency}...")
            
            change_data = {
                "currency_code": target_currency
            }
            
            response = requests.put(
                f"{BASE_URL}/api/v1/company-settings/",
                json=change_data,
                headers=headers
            )
            
            print(f"📊 Código de respuesta: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Cambio de moneda exitoso!")
                updated_settings = response.json()
                new_currency = updated_settings.get("currency_code")
                print(f"✅ Nueva moneda configurada: {new_currency}")
                
                # Update current currency for next iteration
                current_currency = new_currency
                
                # Verify the change persisted
                print("4️⃣ Verificando que el cambio se haya persistido...")
                response = requests.get(f"{BASE_URL}/api/v1/company-settings/", headers=headers)
                if response.status_code == 200:
                    verified_settings = response.json()
                    verified_currency = verified_settings.get("currency_code")
                    if verified_currency == target_currency:
                        print(f"✅ Cambio verificado - Moneda persistida: {verified_currency}")
                    else:
                        print(f"❌ Error en verificación - Esperado: {target_currency}, Actual: {verified_currency}")
                
            else:
                print(f"❌ Error en cambio de moneda!")
                print(f"📋 Respuesta del servidor: {response.text}")
                break
            
            print("-" * 40)
    
    print("\n🎉 Prueba de cambio de moneda completada!")

if __name__ == "__main__":
    test_currency_change()
