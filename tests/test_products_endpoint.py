#!/usr/bin/env python3
"""
Script para probar el endpoint de productos y diagnosticar el error 403
"""

import requests
import json

def test_products_endpoint():
    base_url = "http://localhost:8000"
    
    # Primero intentar hacer login para obtener un token
    login_data = {
        "username": "admin",  # o el usuario que uses
        "password": "admin"   # o la contraseña que uses
    }
    
    print("🔐 Intentando hacer login...")
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Login exitoso, token obtenido")
            
            # Probar el endpoint de productos con autenticación
            headers = {"Authorization": f"Bearer {access_token}"}
            products_url = f"{base_url}/api/v1/products/"
            
            print("📦 Probando endpoint de productos...")
            products_response = requests.get(products_url, headers=headers)
            print(f"Products endpoint status: {products_response.status_code}")
            
            if products_response.status_code == 200:
                data = products_response.json()
                print(f"✅ Endpoint funciona correctamente")
                print(f"Total productos: {data.get('data', {}).get('total', 'N/A')}")
            else:
                print(f"❌ Error en endpoint de productos: {products_response.status_code}")
                print(f"Response: {products_response.text}")
                
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo el backend?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_products_endpoint()
