"""
Script     # Login
    login_payload = {
        "email": "admin@contable.com",
        "password": "Admin123!"
    }
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json=login_payload
    )bar la eliminación bulk desde el frontend
Simula la misma llamada que hace InvoiceListEnhancedPage.tsx
"""
import requests
import json

def test_frontend_bulk_delete():
    """Prueba la eliminación bulk simulando el frontend"""
    
    print("🧪 Probando eliminación bulk desde frontend...")
    
    # Login
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "username": "admin@contable.com",
            "password": "admin123!"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        print(f"Respuesta completa del login:")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener facturas NFE en borrador
    invoices_response = requests.get(
        "http://localhost:8000/api/v1/invoices",
        headers=headers,
        params={
            "status": "DRAFT",
            "page": 1,
            "page_size": 10
        }
    )
    
    if invoices_response.status_code != 200:
        print(f"❌ Error obteniendo facturas: {invoices_response.status_code}")
        return
    
    invoices = invoices_response.json()["items"]
    nfe_invoices = [inv for inv in invoices if "NFe" in inv.get("invoice_number", "")]
    
    if len(nfe_invoices) < 2:
        print("⚠️ No hay suficientes facturas NFE en borrador para probar")
        return
    
    # Seleccionar 2 facturas para eliminar
    selected_invoices = nfe_invoices[:2]
    invoice_ids = [inv["id"] for inv in selected_invoices]
    
    print(f"🎯 Seleccionadas {len(selected_invoices)} facturas NFE:")
    for inv in selected_invoices:
        print(f"   - {inv['invoice_number']} (ID: {inv['id']})")
    
    # Payload exacto como lo envía InvoiceListEnhancedPage.tsx
    payload = {
        "invoice_ids": invoice_ids,
        "confirmation": "CONFIRM_DELETE",
        "reason": "Eliminación bulk desde listado de facturas"
    }
    
    print(f"\n📤 Enviando payload:")
    print(json.dumps(payload, indent=2))
    
    # Hacer la petición DELETE
    response = requests.delete(
        "http://localhost:8000/api/v1/invoices/bulk/delete",
        headers=headers,
        json=payload  # Usar json= en lugar de data=
    )
    
    print(f"\n📥 Respuesta del servidor:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 422:
        print(f"❌ Error de validación (422):")
        try:
            error_detail = response.json()
            print(json.dumps(error_detail, indent=2))
        except:
            print(response.text)
    elif response.status_code == 200:
        result = response.json()
        print(f"✅ Eliminación exitosa:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error inesperado:")
        print(response.text)

if __name__ == "__main__":
    test_frontend_bulk_delete()
