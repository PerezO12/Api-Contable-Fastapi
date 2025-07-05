#!/usr/bin/env python3
"""
Script para probar el flujo completo a través de los endpoints HTTP
Esto simula exactamente lo que haría el frontend
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"  # Ajustar según tu configuración
API_PREFIX = "/api/v1"

def test_http_payment_flow():
    """
    Prueba el flujo completo usando los endpoints HTTP reales
    """
    print("=== Iniciando prueba HTTP del flujo de pagos ===")
    
    # 1. Primer paso: Login para obtener token (opcional según tu implementación)
    session = requests.Session()
    
    # Buscar un pago existente en estado DRAFT para convertir en la prueba
    print("\n--- Paso 1: Obteniendo lista de pagos ---")
    response = session.get(f"{BASE_URL}{API_PREFIX}/payment-flow/payments")
    
    if response.status_code != 200:
        print(f"Error obteniendo pagos: {response.status_code}")
        print(response.text)
        return
    
    payments = response.json()
    
    # Buscar un pago en DRAFT
    draft_payment = None
    for payment in payments:
        if payment.get('status') == 'DRAFT':
            draft_payment = payment
            break
    
    if not draft_payment:
        print("No se encontró ningún pago en estado DRAFT para la prueba")
        return
    
    payment_id = draft_payment['id']
    print(f"Usando pago: {draft_payment['number']} (ID: {payment_id})")
    
    # 2. Confirmar el pago (DRAFT -> POSTED)
    print("\n--- Paso 2: Confirmando pago ---")
    confirm_data = {
        "reason": "Prueba HTTP del problema UNKNOWN"
    }
    
    response = session.post(
        f"{BASE_URL}{API_PREFIX}/payment-flow/confirm/{payment_id}",
        json=confirm_data
    )
    
    if response.status_code != 200:
        print(f"Error confirmando pago: {response.status_code}")
        print(response.text)
        return
    
    confirmed_payment = response.json()
    print(f"✓ Pago confirmado: {confirmed_payment['status']}")
    
    # 3. Resetear el pago a borrador (POSTED -> DRAFT)
    print("\n--- Paso 3: Restableciendo pago a borrador ---")
    reset_data = {
        "reason": "Prueba HTTP del problema UNKNOWN"
    }
    
    response = session.post(
        f"{BASE_URL}{API_PREFIX}/payment-flow/reset/{payment_id}",
        params={"reason": "Prueba HTTP del problema UNKNOWN"}
    )
    
    if response.status_code != 200:
        print(f"Error restableciendo pago: {response.status_code}")
        print(response.text)
        return
    
    reset_payment = response.json()
    print(f"✓ Pago restablecido: {reset_payment['status']}")
    
    # 4. Pequeña pausa para simular el comportamiento real
    print("\n--- Esperando 1 segundo (simular delay del frontend) ---")
    time.sleep(1)
    
    # 5. Validación masiva inmediatamente después del reset
    print("\n--- Paso 4: Validación masiva inmediatamente después del reset ---")
    validation_data = {
        "payment_ids": [payment_id]
    }
    
    response = session.post(
        f"{BASE_URL}{API_PREFIX}/payment-flow/bulk-validate",
        json=validation_data
    )
    
    if response.status_code != 200:
        print(f"Error en validación masiva: {response.status_code}")
        print(response.text)
        return
    
    validation_result = response.json()
    print(f"Resultados de validación HTTP:")
    print(f"  Total pagos: {validation_result['total_payments']}")
    print(f"  Pueden confirmarse: {validation_result['can_confirm_count']}")
    print(f"  Bloqueados: {validation_result['blocked_count']}")
    
    # 6. Revisar resultado específico
    if validation_result['validation_results']:
        result = validation_result['validation_results'][0]
        print(f"\nDetalle del resultado HTTP:")
        print(f"  Payment ID: {result['payment_id']}")
        print(f"  Payment Number: {result['payment_number']}")
        print(f"  Can Confirm: {result['can_confirm']}")
        print(f"  Blocking Reasons: {result['blocking_reasons']}")
        
        if result['payment_number'].startswith("UNKNOWN"):
            print("\n❌ PROBLEMA DETECTADO EN HTTP: El pago aparece como UNKNOWN")
            
            # Intentar validación nuevamente para ver si persiste
            print("\n--- Reintentando validación después de 2 segundos ---")
            time.sleep(2)
            
            response2 = session.post(
                f"{BASE_URL}{API_PREFIX}/payment-flow/bulk-validate",
                json=validation_data
            )
            
            if response2.status_code == 200:
                validation_result2 = response2.json()
                result2 = validation_result2['validation_results'][0] if validation_result2['validation_results'] else None
                
                if result2 and not result2['payment_number'].startswith("UNKNOWN"):
                    print("✓ En segundo intento el pago se encuentra correctamente")
                    print("  → El problema es temporal/de timing")
                else:
                    print("✗ En segundo intento el pago sigue apareciendo como UNKNOWN")
                    print("  → El problema persiste")
        else:
            print("\n✓ Pago validado correctamente en HTTP")
            print("  → No se detectó el problema UNKNOWN")
    
    # 7. Intentar confirmación masiva para completar la prueba
    print("\n--- Paso 5: Intentando confirmación masiva ---")
    bulk_confirm_data = {
        "payment_ids": [payment_id],
        "confirmation_notes": "Prueba HTTP bulk confirm después de reset"
    }
    
    response = session.post(
        f"{BASE_URL}{API_PREFIX}/payment-flow/bulk-confirm",
        json=bulk_confirm_data
    )
    
    if response.status_code == 200:
        bulk_result = response.json()
        print(f"✓ Confirmación masiva exitosa:")
        print(f"  Exitosos: {bulk_result['successful']}")
        print(f"  Fallidos: {bulk_result['failed']}")
    else:
        print(f"Error en confirmación masiva: {response.status_code}")
        print(response.text)
    
    print("\n=== Prueba HTTP completada ===")

if __name__ == "__main__":
    try:
        test_http_payment_flow()
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar al servidor. Asegúrate de que esté ejecutándose en http://localhost:8000")
    except Exception as e:
        print(f"Error durante la prueba HTTP: {str(e)}")
        import traceback
        traceback.print_exc()
