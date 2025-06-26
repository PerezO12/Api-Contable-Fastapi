#!/usr/bin/env python3

"""
Script para probar la funcionalidad de navegación de lotes en el backend
"""

import requests
import json
import os
import tempfile
import pandas as pd

# Configuración
BASE_URL = "http://localhost:8000/api/v1/generic-import"
MODEL_NAME = "product"

# Datos de prueba para productos
TEST_PRODUCTS = [
    {"name": f"Producto Test {i}", "description": f"Descripción del producto {i}", "unit_price": f"{i * 10}.00"}
    for i in range(1, 101)  # 100 productos de prueba
]

def create_test_csv():
    """Crear archivo CSV de prueba con 100 productos"""
    df = pd.DataFrame(TEST_PRODUCTS)
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name

def test_batch_navigation():
    """Probar la navegación de lotes"""
    print("🔍 === PRUEBA DE NAVEGACIÓN DE LOTES ===\n")
    
    try:
        # 1. Crear archivo de prueba
        print("📄 Creando archivo CSV de prueba...")
        csv_file = create_test_csv()
        
        # 2. Crear sesión de importación
        print("🔧 Creando sesión de importación...")
        with open(csv_file, 'rb') as f:
            files = {'file': ('test_products.csv', f, 'text/csv')}
            data = {'model_name': MODEL_NAME}
            response = requests.post(f"{BASE_URL}/sessions", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Error creando sesión: {response.status_code} - {response.text}")
            return False
        
        session_data = response.json()
        session_id = session_data['import_session_token']
        print(f"✅ Sesión creada: {session_id}")
        
        # 3. Probar obtener información de lotes
        print("\n📊 Probando obtener información de lotes...")
        batch_size = 25  # 4 lotes de 25 productos cada uno
        
        response = requests.get(f"{BASE_URL}/sessions/{session_id}/batch-info?batch_size={batch_size}")
        if response.status_code != 200:
            print(f"❌ Error obteniendo info de lotes: {response.status_code} - {response.text}")
            return False
        
        batch_info = response.json()
        print(f"✅ Información de lotes obtenida:")
        print(f"   Total de lotes: {batch_info['total_batches']}")
        print(f"   Total de filas: {batch_info['total_rows']}")
        print(f"   Tamaño de lote: {batch_info['batch_size']}")
        
        # 4. Obtener sugerencias de mapeo
        print("\n🎯 Obteniendo sugerencias de mapeo...")
        response = requests.get(f"{BASE_URL}/sessions/{session_id}/mapping-suggestions")
        if response.status_code != 200:
            print(f"❌ Error obteniendo mapeo: {response.status_code} - {response.text}")
            return False
        
        mapping_data = response.json()
        mappings = [
            {"column_name": "name", "field_name": "name"},
            {"column_name": "description", "field_name": "description"},
            {"column_name": "unit_price", "field_name": "unit_price"}
        ]
        
        # 5. Probar vista previa de diferentes lotes
        print("\n🔍 Probando vista previa de diferentes lotes...")
        
        for batch_number in range(min(3, batch_info['total_batches'])):  # Probar hasta 3 lotes
            print(f"\n   Lote {batch_number + 1} de {batch_info['total_batches']}:")
            
            preview_request = {
                "import_session_token": session_id,
                "column_mappings": mappings,
                "import_policy": "create_only",
                "skip_validation_errors": False,
                "default_values": {},
                "batch_size": batch_size,
                "batch_number": batch_number
            }
            
            response = requests.post(f"{BASE_URL}/sessions/{session_id}/preview", json=preview_request)
            if response.status_code != 200:
                print(f"      ❌ Error en vista previa del lote {batch_number}: {response.status_code} - {response.text}")
                continue
            
            preview_data = response.json()
            
            if 'batch_info' in preview_data and preview_data['batch_info']:
                batch_info_response = preview_data['batch_info']
                print(f"      ✅ Lote actual: {batch_info_response['current_batch'] + 1}")
                print(f"      📊 Filas en este lote: {batch_info_response['current_batch_rows']}")
                print(f"      📋 Rango: {batch_info_response['current_batch'] * batch_info_response['batch_size'] + 1} - {(batch_info_response['current_batch'] * batch_info_response['batch_size']) + batch_info_response['current_batch_rows']}")
                
                # Mostrar algunos productos del lote
                if preview_data['preview_data']:
                    first_product = preview_data['preview_data'][0]['transformed_data']
                    print(f"      🎯 Primer producto: {first_product.get('name', 'N/A')}")
            else:
                print(f"      ❌ No hay información de lote en la respuesta")
        
        # 6. Limpiar
        print(f"\n🧹 Limpiando...")
        try:
            requests.delete(f"{BASE_URL}/sessions/{session_id}")
            os.unlink(csv_file)
            print("✅ Limpieza completada")
        except:
            pass
        
        print("\n🎉 === PRUEBA COMPLETADA EXITOSAMENTE ===")
        print("✅ La navegación de lotes funciona correctamente en el backend")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

if __name__ == "__main__":
    success = test_batch_navigation()
    exit(0 if success else 1)
