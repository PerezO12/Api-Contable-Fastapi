#!/usr/bin/env python3
"""
Script para probar que el endpoint /invoices/{id}/with-lines
retorna correctamente la información de productos en las líneas
"""
import sys
import os
import requests
import json

def test_invoice_with_lines_endpoint():
    """
    Prueba el endpoint de facturas con líneas para verificar
    que incluye información de productos
    """
    # URL del endpoint (asumiendo que el servidor está corriendo en puerto 8000)
    base_url = "http://localhost:8000"
    
    # ID de la factura de ejemplo que proporcionaste
    invoice_id = "bf85f55a-5ea6-46cc-ae7a-e2db2ba7e6c5"
    
    # Hacer la petición al endpoint
    url = f"{base_url}/api/v1/invoices/{invoice_id}/with-lines"
    
    print(f"🔍 Probando endpoint: {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Respuesta exitosa (HTTP {response.status_code})")
            print(f"📄 Factura: {data.get('invoice_number', 'N/A')}")
            print(f"📝 Líneas encontradas: {len(data.get('lines', []))}")
            
            # Verificar las líneas
            lines = data.get('lines', [])
            
            for i, line in enumerate(lines):
                print(f"\n--- Línea {i + 1} ---")
                print(f"  ID: {line.get('id', 'N/A')}")
                print(f"  Descripción: {line.get('description', 'N/A')}")
                print(f"  Producto ID: {line.get('product_id', 'N/A')}")
                print(f"  Producto Nombre: {line.get('product_name', 'N/A')}")
                print(f"  Producto Código: {line.get('product_code', 'N/A')}")
                
                # Verificar si tiene información del producto
                if line.get('product_id') and line.get('product_name'):
                    print(f"  ✅ Información del producto incluida correctamente")
                elif line.get('product_id') and not line.get('product_name'):
                    print(f"  ❌ Producto ID presente pero falta nombre/código")
                else:
                    print(f"  ℹ️  Línea sin producto asociado")
            
            # Mostrar la respuesta completa para debug
            print(f"\n📋 Respuesta completa:")
            print(json.dumps(data, indent=2))
            
        elif response.status_code == 404:
            print(f"❌ Factura no encontrada (HTTP {response.status_code})")
            print("ℹ️  Verifique que el ID de la factura sea correcto")
            
        else:
            print(f"❌ Error en la respuesta (HTTP {response.status_code})")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor backend")
        print("ℹ️  Verifique que el servidor esté ejecutándose en http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")


if __name__ == "__main__":
    print("🧪 Probando endpoint /invoices/{id}/with-lines...")
    test_invoice_with_lines_endpoint()
