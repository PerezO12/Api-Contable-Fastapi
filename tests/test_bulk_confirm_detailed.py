#!/usr/bin/env python3
"""
Script para probar el servicio de pagos con logs detallados
"""
import requests
import json
import sys

def test_bulk_confirm_api():
    """Test del endpoint bulk confirm con logs detallados"""
    
    print("🔧 Testing bulk confirm API with detailed logging...")
    
    # URL del endpoint
    base_url = "http://127.0.0.1:8000"
    endpoint = f"{base_url}/api/v1/payments/bulk/confirm"
    
    # Datos de prueba (usar UUIDs reales de tu base de datos)
    test_data = {
        "payment_ids": [
            "00000000-0000-0000-0000-000000000001",  # UUID de prueba - reemplazar con IDs reales
            "00000000-0000-0000-0000-000000000002"   # UUID de prueba - reemplazar con IDs reales
        ],
        "confirmation_notes": "Test bulk confirm with detailed logging",
        "force": False
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Reemplazar con token real
    }
    
    try:
        print(f"📡 Making POST request to: {endpoint}")
        print(f"📋 Request data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            endpoint, 
            json=test_data, 
            headers=headers, 
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            print(f"📋 Response data: {json.dumps(response.json(), indent=2)}")
        elif response.status_code == 422:
            print("❌ Request failed with 422 Unprocessable Entity")
            print(f"📋 Error response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📋 Response text: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"💥 JSON decode error: {e}")
        print(f"📋 Response text: {response.text}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

def print_test_instructions():
    """Muestra instrucciones para usar el script"""
    print("📋 Instructions for testing:")
    print("1. Make sure your API server is running on http://127.0.0.1:8000")
    print("2. Replace the payment_ids in the script with real UUIDs from your database")
    print("3. Replace 'YOUR_TOKEN_HERE' with a valid authentication token")
    print("4. Run the script and check both the console output and server logs")
    print("5. Look for detailed logs in the server console starting with:")
    print("   🚀 [API_BULK_CONFIRM], 🔍 [VALIDATE_BULK], ✅ [CONFIRM_PAYMENT], etc.")

if __name__ == "__main__":
    print_test_instructions()
    print("\n" + "="*50 + "\n")
    test_bulk_confirm_api()
