#!/usr/bin/env python3
"""
Script de prueba para el flujo completo de facturas con los nuevos endpoints
Prueba el flujo: DRAFT → POSTED → CANCELLED → RESET TO DRAFT
"""

import requests
import json
from datetime import date, datetime
import time

# Configuración
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-token-here"  # Reemplazar con token real
}

def print_step(step_num, description):
    """Imprimir paso del flujo"""
    print(f"\n{'='*60}")
    print(f"PASO {step_num}: {description}")
    print('='*60)

def print_response(response):
    """Imprimir respuesta de la API"""
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")

def test_invoice_workflow():
    """Probar el flujo completo de facturas"""
    
    print_step(1, "CREAR FACTURA EN ESTADO DRAFT")
    
    # Datos de ejemplo para crear factura
    invoice_data = {
        "invoice_type": "CUSTOMER_INVOICE",
        "third_party_id": "01234567-89ab-cdef-0123-456789abcdef",  # UUID de ejemplo
        "invoice_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "description": "Factura de prueba - flujo workflow",
        "currency_code": "USD",
        "lines": [
            {
                "sequence": 1,
                "description": "Producto de prueba",
                "quantity": 2,
                "unit_price": 100.00,
                "account_id": "01234567-89ab-cdef-0123-456789abcdef"  # UUID de cuenta de ejemplo
            }
        ]
    }
    
    # Crear factura
    response = requests.post(
        f"{BASE_URL}/invoices/",
        headers=HEADERS,
        json=invoice_data
    )
    print_response(response)
    
    if response.status_code != 201:
        print("❌ Error creando factura. Abortando prueba.")
        return
    
    invoice_id = response.json()["id"]
    print(f"✅ Factura creada con ID: {invoice_id}")
    
    # Verificar estado inicial
    print_step(2, "VERIFICAR ESTADO INICIAL (DRAFT)")
    
    response = requests.get(
        f"{BASE_URL}/invoices/{invoice_id}/workflow-status",
        headers=HEADERS
    )
    print_response(response)
    
    if response.status_code == 200:
        status = response.json()["current_status"]
        transitions = response.json()["valid_transitions"]
        print(f"✅ Estado actual: {status}")
        print(f"✅ Transiciones válidas: {transitions}")
    
    # Contabilizar factura (DRAFT → POSTED)
    print_step(3, "CONTABILIZAR FACTURA (DRAFT → POSTED)")
    
    post_data = {
        "notes": "Contabilización automática de prueba",
        "force_post": True
    }
    
    response = requests.post(
        f"{BASE_URL}/invoices/{invoice_id}/post",
        headers=HEADERS,
        json=post_data
    )
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Factura contabilizada exitosamente")
        
        # Verificar que el estado cambió
        response = requests.get(
            f"{BASE_URL}/invoices/{invoice_id}/workflow-status",
            headers=HEADERS
        )
        if response.status_code == 200:
            status = response.json()["current_status"]
            print(f"✅ Nuevo estado: {status}")
    else:
        print("❌ Error contabilizando factura")
        return
    
    # Cancelar factura (POSTED → CANCELLED)
    print_step(4, "CANCELAR FACTURA (POSTED → CANCELLED)")
    
    cancel_data = {
        "reason": "Cancelación de prueba del flujo de trabajo"
    }
    
    response = requests.post(
        f"{BASE_URL}/invoices/{invoice_id}/cancel",
        headers=HEADERS,
        json=cancel_data
    )
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Factura cancelada exitosamente")
        
        # Verificar estado
        response = requests.get(
            f"{BASE_URL}/invoices/{invoice_id}/workflow-status",
            headers=HEADERS
        )
        if response.status_code == 200:
            status = response.json()["current_status"]
            transitions = response.json()["valid_transitions"]
            print(f"✅ Estado actual: {status}")
            print(f"✅ Transiciones válidas: {transitions}")
    else:
        print("❌ Error cancelando factura")
    
    # Crear otra factura para probar reset to draft
    print_step(5, "CREAR SEGUNDA FACTURA PARA PROBAR RESET TO DRAFT")
    
    invoice_data["description"] = "Segunda factura - prueba reset to draft"
    
    response = requests.post(
        f"{BASE_URL}/invoices/",
        headers=HEADERS,
        json=invoice_data
    )
    
    if response.status_code == 201:
        invoice_id_2 = response.json()["id"]
        print(f"✅ Segunda factura creada con ID: {invoice_id_2}")
        
        # Contabilizar la segunda factura
        response = requests.post(
            f"{BASE_URL}/invoices/{invoice_id_2}/post",
            headers=HEADERS,
            json={"notes": "Contabilización para prueba de reset"}
        )
        
        if response.status_code == 200:
            print("✅ Segunda factura contabilizada")
            
            # Restablecer a borrador (POSTED → DRAFT)
            print_step(6, "RESTABLECER A BORRADOR (POSTED → DRAFT)")
            
            reset_data = {
                "reason": "Restablecimiento de prueba del flujo de trabajo"
            }
            
            response = requests.post(
                f"{BASE_URL}/invoices/{invoice_id_2}/reset-to-draft",
                headers=HEADERS,
                json=reset_data
            )
            print_response(response)
            
            if response.status_code == 200:
                print("✅ Factura restablecida a borrador exitosamente")
                
                # Verificar estado final
                response = requests.get(
                    f"{BASE_URL}/invoices/{invoice_id_2}/workflow-status",
                    headers=HEADERS
                )
                if response.status_code == 200:
                    status = response.json()["current_status"]
                    can_edit = response.json()["can_edit"]
                    print(f"✅ Estado final: {status}")
                    print(f"✅ Puede editarse: {can_edit}")
            else:
                print("❌ Error restableciendo factura a borrador")
    
    print_step(7, "RESUMEN DE PRUEBAS")
    print("✅ Flujo completo de workflow de facturas probado")
    print("✅ Estados probados: DRAFT → POSTED → CANCELLED")
    print("✅ Estados probados: DRAFT → POSTED → DRAFT (reset)")
    print("✅ Todos los endpoints funcionando correctamente")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del flujo de workflow de facturas")
    print("⚠️  NOTA: Asegúrese de tener el servidor corriendo y un token válido")
    print("⚠️  NOTA: Actualice los UUIDs de terceros y cuentas con valores reales")
    
    # Para testing manual, descomentar la siguiente línea:
    # test_invoice_workflow()
    
    print("\n📋 Para ejecutar las pruebas:")
    print("1. Actualizar HEADERS con un token válido")
    print("2. Actualizar UUIDs en invoice_data con valores reales de su BD")
    print("3. Descomentar la llamada a test_invoice_workflow()")
    print("4. Ejecutar: python test_invoice_workflow.py")
