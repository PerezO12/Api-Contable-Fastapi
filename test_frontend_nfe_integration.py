#!/usr/bin/env python3
"""
Test simple para verificar que el frontend muestra correctamente 
la información de facturas NFE en operaciones bulk
"""

import httpx
import time

# Configuración
BASE_URL = "http://localhost:8000"
TEST_CREDENTIALS = {
    "email": "admin@contable.com",
    "password": "Admin123!"
}

def test_nfe_invoices_display():
    """Test para verificar que hay facturas NFE disponibles en el sistema"""
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)
    
    # Login
    response = client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Error en login: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    # Buscar facturas en estado DRAFT
    response = client.get("/api/v1/invoices/", params={
        "page": 1,
        "page_size": 50,
        "status": "DRAFT"
    })
    
    if response.status_code == 200:
        result = response.json()
        invoices = result.get('items', [])
        
        # Filtrar facturas NFE
        nfe_invoices = [inv for inv in invoices if 'NFe' in inv.get('invoice_number', '')]
        
        print(f"📊 ESTADO DE FACTURAS PARA TESTING:")
        print(f"   Total facturas en DRAFT: {len(invoices)}")
        print(f"   Facturas NFE en DRAFT: {len(nfe_invoices)}")
        
        if nfe_invoices:
            print(f"\n✅ El frontend debería mostrar información de NFE para {len(nfe_invoices)} facturas")
            print("📋 Ejemplos de facturas NFE:")
            for inv in nfe_invoices[:3]:  # Mostrar solo las primeras 3
                print(f"   - {inv.get('invoice_number')}: ${inv.get('total_amount', 0)}")
            print(f"\n💡 INSTRUCCIONES PARA TESTING:")
            print(f"   1. Abrir http://localhost:3000/invoices en el navegador")
            print(f"   2. Seleccionar algunas facturas NFE (que contengan 'NFe' en el número)")
            print(f"   3. Hacer clic en 'Eliminar' en la barra de acciones bulk")
            print(f"   4. Verificar que aparezca el mensaje sobre facturas NFE")
            print(f"   5. Confirmar la eliminación")
            print(f"   6. Verificar el mensaje de éxito con información de NFE")
        else:
            print("⚠️ No hay facturas NFE en DRAFT para probar")
            print("💡 Ejecuta primero test_nfe_import.py para crear facturas NFE")
            
    else:
        print(f"❌ Error al buscar facturas: {response.status_code}")

if __name__ == "__main__":
    test_nfe_invoices_display()
