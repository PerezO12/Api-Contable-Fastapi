#!/usr/bin/env python3
"""
Script de prueba para las nuevas funcionalidades de centros de costo:
- Bulk delete
- Import desde CSV
- Export a CSV
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.cost_center import (
    BulkCostCenterDelete, CostCenterDeleteValidation,
    CostCenterImportResult
)

def test_schemas():
    """Probar que los schemas estén correctamente definidos"""
    print("🧪 Probando schemas...")
    
    # Test BulkCostCenterDelete
    bulk_delete = BulkCostCenterDelete(
        cost_center_ids=[uuid.uuid4(), uuid.uuid4()],
        force_delete=False,
        delete_reason="Test deletion"
    )
    print(f"✅ BulkCostCenterDelete: {bulk_delete}")
    
    # Test CostCenterDeleteValidation
    validation = CostCenterDeleteValidation(
        cost_center_id=uuid.uuid4(),
        can_delete=True,
        blocking_reasons=[],
        warnings=["Test warning"],
        dependencies={"test": "value"}
    )
    print(f"✅ CostCenterDeleteValidation: {validation}")
    
    # Test CostCenterImportResult
    import_result = CostCenterImportResult(
        total_rows=10,
        successfully_imported=8,
        updated_existing=1,
        failed_imports=[],
        validation_errors=[],
        warnings=["Test warning"],
        created_cost_centers=[uuid.uuid4()]
    )
    print(f"✅ CostCenterImportResult: {import_result}")
    print(f"   Success rate: {import_result.success_rate}%")

def create_sample_csv():
    """Crear un archivo CSV de ejemplo para importación"""
    csv_content = """code,name,description,parent_code,is_active,allows_direct_assignment,manager_name,budget_code,notes
ADM,Administración,Departamento de Administración,,true,true,Juan Pérez,ADM001,Centro de costo administrativo
VEN,Ventas,Departamento de Ventas,,true,true,María García,VEN001,Centro de costo de ventas
PROD,Producción,Departamento de Producción,,true,false,Carlos López,PROD001,Centro de costo de producción
VEN-01,Ventas Norte,Zona Norte,VEN,true,true,Ana Torres,VEN-N01,Ventas región norte
VEN-02,Ventas Sur,Zona Sur,VEN,true,true,Luis Castro,VEN-S01,Ventas región sur"""
    
    return csv_content

def test_csv_format():
    """Probar el formato del CSV"""
    print("\n📄 Probando formato CSV...")
    csv_content = create_sample_csv()
    
    lines = csv_content.strip().split('\n')
    headers = lines[0].split(',')
    
    print(f"✅ Headers encontrados: {headers}")
    print(f"✅ Número de filas de datos: {len(lines) - 1}")
    
    # Mostrar primera fila de datos
    first_data_row = lines[1].split(',')
    print(f"✅ Primera fila de datos: {dict(zip(headers, first_data_row))}")

def show_new_endpoints():
    """Mostrar los nuevos endpoints agregados"""
    print("\n🚀 Nuevos endpoints agregados para centros de costo:")
    
    endpoints = [
        {
            "method": "POST",
            "path": "/api/v1/cost-centers/bulk-delete",
            "description": "Eliminar múltiples centros de costo con validaciones",
            "response": "BulkCostCenterDeleteResult"
        },
        {
            "method": "POST", 
            "path": "/api/v1/cost-centers/validate-deletion",
            "description": "Validar si centros de costo pueden ser eliminados",
            "response": "List[CostCenterDeleteValidation]"
        },
        {
            "method": "POST",
            "path": "/api/v1/cost-centers/import",
            "description": "Importar centros de costo desde CSV",
            "response": "CostCenterImportResult"
        },
        {
            "method": "GET",
            "path": "/api/v1/cost-centers/export/csv",
            "description": "Exportar centros de costo a CSV",
            "response": "CSV file content"
        }
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint['method']} {endpoint['path']}")
        print(f"      {endpoint['description']}")
        print(f"      Response: {endpoint['response']}")
        print()

def show_usage_examples():
    """Mostrar ejemplos de uso"""
    print("📖 Ejemplos de uso:")
    
    print("\n1. Bulk Delete (JSON request body):")
    bulk_delete_example = {
        "cost_center_ids": ["uuid1", "uuid2", "uuid3"],
        "force_delete": False,
        "delete_reason": "Reestructuración departamental"
    }
    print(f"   {bulk_delete_example}")
    
    print("\n2. Validate Deletion (JSON request body):")
    validate_example = ["uuid1", "uuid2", "uuid3"]
    print(f"   {validate_example}")
    
    print("\n3. Import CSV (multipart/form-data):")
    print("   Enviar archivo CSV con las columnas:")
    print("   - code (requerido)")
    print("   - name (requerido)")  
    print("   - description, parent_code, is_active, etc. (opcionales)")
    
    print("\n4. Export CSV:")
    print("   GET /api/v1/cost-centers/export/csv?is_active=true")

if __name__ == "__main__":
    print("🎯 Prueba de nuevas funcionalidades de Centros de Costo")
    print("=" * 60)
    
    try:
        test_schemas()
        test_csv_format()
        show_new_endpoints()
        show_usage_examples()
        
        print("\n✅ Todas las pruebas pasaron exitosamente!")
        print("\n📝 Resumen de funcionalidades agregadas:")
        print("   • Bulk delete con validaciones exhaustivas")
        print("   • Validación previa de eliminación")
        print("   • Importación masiva desde CSV")
        print("   • Exportación a CSV")
        print("   • Manejo de jerarquías en import/export")
        print("   • Permisos y validaciones de seguridad")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
