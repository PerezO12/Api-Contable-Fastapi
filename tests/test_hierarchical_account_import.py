#!/usr/bin/env python3
"""
Prueba del servicio de importación jerárquica de cuentas
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.hierarchical_account_import_service import HierarchicalAccountImportService


async def test_topological_sorting():
    """Prueba el ordenamiento topológico de cuentas con dependencias"""
    
    # Crear datos de prueba con dependencias padre-hijo desordenadas
    account_data_desordenada = [
        {
            "code": "1111",
            "name": "CAJA GENERAL",
            "account_type": "activo",
            "parent_code": "1110",  # Depende de 1110 que viene después
            "allows_movements": True
        },
        {
            "code": "1000",
            "name": "ACTIVOS",
            "account_type": "activo",
            "allows_movements": False
        },
        {
            "code": "1110",
            "name": "DISPONIBLE",
            "account_type": "activo",
            "parent_code": "1100",  # Depende de 1100 que viene después
            "allows_movements": False
        },
        {
            "code": "1100",
            "name": "ACTIVOS CORRIENTES", 
            "account_type": "activo",
            "parent_code": "1000",  # Depende de 1000 que ya vino antes
            "allows_movements": False
        },
        {
            "code": "1112",
            "name": "CAJA MENOR",
            "account_type": "activo",
            "parent_code": "1110",  # Depende de 1110
            "allows_movements": True
        }
    ]
    
    # Crear servicio mock (sin base de datos)
    service = HierarchicalAccountImportService(None)  # type: ignore
    
    # Verificar que la validación funciona
    try:
        validated_accounts = await service._validate_account_data(account_data_desordenada)
        print("✓ Validación de datos pasó correctamente")
        print(f"  - {len(validated_accounts)} cuentas validadas")
    except Exception as e:
        print(f"✗ Error en validación: {e}")
        return False
    
    # Verificar que el ordenamiento topológico funciona
    try:
        ordered_accounts = service._topological_sort(validated_accounts)
        print("✓ Ordenamiento topológico exitoso")
        
        # Verificar el orden correcto
        codes_ordenados = [acc["code"] for acc in ordered_accounts]
        print(f"  - Orden original: {[acc['code'] for acc in account_data_desordenada]}")
        print(f"  - Orden topológico: {codes_ordenados}")
        
        # Verificar que el orden es correcto
        orden_esperado = ["1000", "1100", "1110", "1111", "1112"]
        if codes_ordenados == orden_esperado:
            print("✓ El orden topológico es correcto")
        else:
            print(f"✗ El orden topológico es incorrecto. Esperado: {orden_esperado}")
            return False
            
    except Exception as e:
        print(f"✗ Error en ordenamiento topológico: {e}")
        return False
    
    return True


async def test_circular_dependency_detection():
    """Prueba la detección de dependencias circulares"""
    
    # Crear datos con dependencia circular
    account_data_circular = [
        {
            "code": "1000",
            "name": "ACTIVOS",
            "account_type": "activo",
            "parent_code": "1100",  # Depende de 1100
            "allows_movements": False
        },
        {
            "code": "1100",
            "name": "ACTIVOS CORRIENTES",
            "account_type": "activo", 
            "parent_code": "1000",  # Depende de 1000 - CIRCULAR!
            "allows_movements": False
        }
    ]
    
    # Crear servicio mock
    service = HierarchicalAccountImportService(None)  # type: ignore
    
    try:
        validated_accounts = await service._validate_account_data(account_data_circular)
        ordered_accounts = service._topological_sort(validated_accounts)
        print("✗ Debería haber detectado dependencia circular")
        return False
    except ValueError as e:
        if "circular" in str(e).lower():
            print("✓ Dependencia circular detectada correctamente")
            print(f"  - Error: {e}")
            return True
        else:
            print(f"✗ Error inesperado: {e}")
            return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


async def test_missing_parent_detection():
    """Prueba la detección de cuentas padre faltantes"""
    
    # Crear datos con cuenta padre inexistente
    account_data_missing_parent = [
        {
            "code": "1100",
            "name": "ACTIVOS CORRIENTES",
            "account_type": "activo",
            "parent_code": "9999",  # Padre inexistente
            "allows_movements": False
        }
    ]
    
    # Crear servicio mock
    service = HierarchicalAccountImportService(None)  # type: ignore
    
    try:
        validated_accounts = await service._validate_account_data(account_data_missing_parent)
        ordered_accounts = service._topological_sort(validated_accounts)
        print("✗ Debería haber detectado cuenta padre faltante")
        return False
    except ValueError as e:
        if "no encontrada" in str(e).lower():
            print("✓ Cuenta padre faltante detectada correctamente")
            print(f"  - Error: {e}")
            return True
        else:
            print(f"✗ Error inesperado: {e}")
            return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


async def main():
    """Función principal de prueba"""
    print("=== PRUEBAS DEL SERVICIO DE IMPORTACIÓN JERÁRQUICA DE CUENTAS ===")
    print()
    
    tests = [
        ("Ordenamiento topológico", test_topological_sorting),
        ("Detección de dependencias circulares", test_circular_dependency_detection),
        ("Detección de cuentas padre faltantes", test_missing_parent_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Ejecutando: {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                print("PASÓ ✓")
            else:
                print("FALLÓ ✗")
        except Exception as e:
            print(f"ERROR ✗: {e}")
        print()
    
    print(f"=== RESULTADOS: {passed}/{total} pruebas pasaron ===")
    
    if passed == total:
        print("¡Todas las pruebas pasaron! ✓")
        return 0
    else:
        print("Algunas pruebas fallaron ✗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
