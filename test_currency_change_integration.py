"""
Test de integración para el cambio de moneda base de la empresa.
Este script prueba el flujo completo de cambio de moneda incluyendo:
- Validación de existencia de moneda objetivo
- Análisis de asientos históricos
- Creación de asientos de ajuste
- Actualización de configuración
"""
import asyncio
import httpx
import json
from typing import Dict, Any

# Configuración del servidor
BASE_URL = "http://localhost:8000"

async def test_currency_change():
    """Prueba el cambio de moneda base"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Iniciando test de cambio de moneda...")
        
        # 0. Autenticación
        print("\n0️⃣ Autenticándose...")
        login_data = {
            "email": "admin@contable.com",
            "password": "Admin123!"
        }
        
        response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Error en autenticación: {response.status_code}")
            print(response.text)
            return
        
        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Autenticación exitosa")
        
        # 1. Obtener configuración actual
        print("\n1️⃣ Obteniendo configuración actual...")
        response = await client.get(f"{BASE_URL}/api/v1/company-settings/", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo configuración: {response.status_code}")
            print(response.text)
            return
        
        current_settings = response.json()
        current_currency = current_settings.get("currency_code", "USD")
        print(f"✅ Moneda actual: {current_currency}")
        
        # 2. Listar monedas disponibles
        print("\n2️⃣ Obteniendo monedas disponibles...")
        response = await client.get(f"{BASE_URL}/api/v1/currencies/", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo monedas: {response.status_code}")
            print(response.text)
            return
        
        currencies = response.json()
        print(f"✅ Monedas disponibles: {len(currencies.get('items', currencies))}")
        
        # Encontrar una moneda diferente para probar
        target_currency = None
        
        # Verificar si currencies es una lista o dict
        currency_list = currencies.get("items", []) if isinstance(currencies, dict) else currencies
        
        for currency in currency_list:
            if currency["code"] != current_currency and currency["is_active"]:
                target_currency = currency["code"]
                break
        
        if not target_currency:
            print("⚠️ No se encontró una moneda diferente activa para probar")
            # Intentar usar EUR directamente
            target_currency = "EUR"
            print(f"🎯 Usando EUR como moneda objetivo")
        
        print(f"🎯 Moneda objetivo para testing: {target_currency}")
        
        # 3. Intentar cambio de moneda
        print(f"\n3️⃣ Intentando cambio de moneda de {current_currency} a {target_currency}...")
        
        update_data = {
            "currency_code": target_currency
        }
        
        response = await client.put(
            f"{BASE_URL}/api/v1/company-settings/",
            json=update_data,
            headers=headers
        )
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Cambio de moneda exitoso!")
            result = response.json()
            print(f"✅ Nueva moneda configurada: {result.get('currency_code')}")
            
        elif response.status_code == 422:
            print("⚠️ Error de validación (esperado en algunos casos)")
            error_detail = response.json()
            print(f"📋 Detalles del error: {json.dumps(error_detail, indent=2)}")
            
        elif response.status_code == 400:
            print("⚠️ Error de reglas de negocio (esperado)")
            error_detail = response.json()
            print(f"📋 Detalles del error: {json.dumps(error_detail, indent=2)}")
            
        elif response.status_code == 500:
            print("❌ Error 500 - El bug aún existe!")
            print(f"📋 Respuesta del servidor: {response.text}")
            
        else:
            print(f"⚠️ Código de respuesta inesperado: {response.status_code}")
            print(f"📋 Respuesta: {response.text}")
        
        # 4. Verificar estado final
        print("\n4️⃣ Verificando estado final...")
        response = await client.get(f"{BASE_URL}/api/v1/company-settings/", headers=headers)
        
        if response.status_code == 200:
            final_settings = response.json()
            final_currency = final_settings.get("currency_code")
            print(f"✅ Moneda final: {final_currency}")
            
            if final_currency == target_currency:
                print("🎉 Cambio de moneda completado exitosamente!")
            else:
                print(f"ℹ️ Moneda se mantuvo como: {final_currency}")
        else:
            print(f"❌ Error verificando estado final: {response.status_code}")

async def main():
    """Función principal del test"""
    try:
        await test_currency_change()
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Test de integración - Cambio de moneda base")
    print("=" * 50)
    asyncio.run(main())
