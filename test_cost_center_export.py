#!/usr/bin/env python3
"""
Script de prueba para el endpoint de exportación de centros de costo
"""
import asyncio
import sys
sys.path.append('.')

from app.database import AsyncSessionLocal
from app.services.cost_center_service import CostCenterService


async def test_cost_center_export():
    """Probar la exportación de centros de costo a CSV"""
    async with AsyncSessionLocal() as db:
        service = CostCenterService(db)
        
        print("=== Probando exportación de centros de costo ===")
        
        # Test 1: Exportar todos los centros de costo
        print("\n1. Exportar todos los centros de costo:")
        try:
            csv_content = await service.export_cost_centers_to_csv()
            
            if csv_content:
                lines = csv_content.strip().split('\n')
                print(f"   ✅ CSV generado exitosamente")
                print(f"   📊 Total de líneas: {len(lines)}")
                print(f"   📄 Encabezados: {lines[0] if lines else 'N/A'}")
                
                # Mostrar las primeras 3 filas de datos (sin encabezado)
                if len(lines) > 1:
                    print(f"   📋 Primeras filas de datos:")
                    for i, line in enumerate(lines[1:4], 1):
                        # Solo mostrar los primeros campos para no sobrecargar
                        fields = line.split(',')
                        code = fields[0] if len(fields) > 0 else 'N/A'
                        name = fields[1] if len(fields) > 1 else 'N/A'
                        active = fields[3] if len(fields) > 3 else 'N/A'
                        print(f"      {i}. Código: {code}, Nombre: {name}, Activo: {active}")
                
                # Mostrar estadísticas
                data_rows = len(lines) - 1  # Sin contar encabezado
                print(f"   📈 Total de centros de costo exportados: {data_rows}")
                
            else:
                print("   ❌ No se generó contenido CSV")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test 2: Exportar solo centros de costo activos
        print("\n2. Exportar solo centros de costo activos:")
        try:
            csv_content_active = await service.export_cost_centers_to_csv(is_active=True)
            
            if csv_content_active:
                lines_active = csv_content_active.strip().split('\n')
                data_rows_active = len(lines_active) - 1
                print(f"   ✅ CSV de activos generado exitosamente")
                print(f"   📈 Total de centros de costo activos: {data_rows_active}")
            else:
                print("   ❌ No se generó contenido CSV para activos")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test 3: Exportar solo centros de costo inactivos
        print("\n3. Exportar solo centros de costo inactivos:")
        try:
            csv_content_inactive = await service.export_cost_centers_to_csv(is_active=False)
            
            if csv_content_inactive:
                lines_inactive = csv_content_inactive.strip().split('\n')
                data_rows_inactive = len(lines_inactive) - 1
                print(f"   ✅ CSV de inactivos generado exitosamente")
                print(f"   📈 Total de centros de costo inactivos: {data_rows_inactive}")
            else:
                print("   ℹ️  No hay centros de costo inactivos para exportar")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("\n=== Pruebas de exportación completadas ===")


if __name__ == "__main__":
    asyncio.run(test_cost_center_export())
