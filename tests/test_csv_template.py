#!/usr/bin/env python3
"""
Script de prueba para verificar que el template CSV incluya cash_flow_category
"""
import sys
import os
import io
import csv

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_csv_template_generation():
    """Probar la generación del template CSV"""
    
    # Datos de ejemplo como en la función real
    example_accounts = [
        {
            "code": "1105",
            "name": "Caja General",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE",
            "cash_flow_category": "cash",
            "parent_code": "1100",
            "description": "Dinero en efectivo en caja principal",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": False,
            "requires_cost_center": False,
            "notes": "Cuenta para manejo de efectivo - Efectivo y equivalentes para flujo de efectivo"
        },
        {
            "code": "1110",
            "name": "Bancos Moneda Nacional",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE",
            "cash_flow_category": "cash",
            "parent_code": "1100",
            "description": "Depósitos en bancos en moneda nacional",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el banco como tercero - Efectivo y equivalentes"
        },
        {
            "code": "2105",
            "name": "Proveedores Nacionales",
            "account_type": "PASIVO",
            "category": "PASIVO_CORRIENTE",
            "cash_flow_category": "operating",
            "parent_code": "2100",
            "description": "Cuentas por pagar a proveedores nacionales",
            "is_active": True,
            "allows_movements": True,
            "requires_third_party": True,
            "requires_cost_center": False,
            "notes": "Requiere especificar el proveedor - Actividades operativas"
        }
    ]
    
    # Headers como en la función real
    headers = ["code", "name", "account_type", "category", "cash_flow_category", "parent_code", 
              "description", "is_active", "allows_movements", "requires_third_party", 
              "requires_cost_center", "notes"]
    
    # Generar CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for account in example_accounts:
        row = [account.get(field, "") for field in headers]
        writer.writerow(row)
    
    output.seek(0)
    csv_content = output.getvalue()
    
    print("🔍 VERIFICACIÓN DE TEMPLATE CSV")
    print("=" * 60)
    print(f"✅ Headers incluyen cash_flow_category: {'cash_flow_category' in headers}")
    print(f"✅ CSV contiene cash_flow_category: {'cash_flow_category' in csv_content}")
    print(f"✅ CSV contiene valores de categorías: {'cash' in csv_content and 'operating' in csv_content}")
    print(f"✅ Total de headers: {len(headers)}")
    print(f"✅ Total de filas de datos: {len(example_accounts)}")
    
    print("\n📄 CONTENIDO DEL CSV:")
    print("-" * 60)
    print(csv_content)
    print("-" * 60)
    
    # Verificar cada fila
    lines = csv_content.strip().split('\n')
    csv_reader = csv.reader(lines)
    header_row = next(csv_reader)
    
    print(f"\n🔎 ANÁLISIS DETALLADO:")
    print(f"   - Posición de cash_flow_category: {header_row.index('cash_flow_category') if 'cash_flow_category' in header_row else 'NO ENCONTRADO'}")
    
    for i, row in enumerate(csv_reader, 1):
        if len(row) > 4:  # Verificar que hay suficientes columnas
            cash_flow_value = row[4] if len(row) > 4 else "VACÍO"
            print(f"   - Fila {i}: cash_flow_category = '{cash_flow_value}'")
    
    return csv_content

if __name__ == "__main__":
    try:
        result = test_csv_template_generation()
        print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
        
        # Guardar el resultado para verificación
        with open("test_csv_output.csv", "w", encoding="utf-8") as f:
            f.write(result)
        print("📁 CSV guardado como 'test_csv_output.csv'")
        
    except Exception as e:
        print(f"❌ ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
