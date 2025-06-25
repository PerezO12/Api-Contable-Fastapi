#!/usr/bin/env python3
"""
Prueba de importación de cuentas con el nuevo campo allows_reconciliation
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.model_metadata_registry import ModelMetadataRegistry


async def test_account_metadata():
    """Prueba que el metadata de cuentas incluya los nuevos campos"""
    
    print("🧪 Probando metadata de cuentas con nuevos campos...")
    
    # Crear instancia del registry
    registry = ModelMetadataRegistry()
    
    # Obtener metadata de cuentas
    try:
        account_metadata = registry.get_model_metadata("account")
        print(f"✅ Metadata de cuenta obtenido: {account_metadata.display_name}")
        
        # Verificar que los campos nuevos estén presentes
        field_names = [field.internal_name for field in account_metadata.fields]
        
        expected_fields = [
            "code",
            "name", 
            "account_type",
            "category",
            "cash_flow_category",
            "allows_reconciliation",
            "allows_movements",
            "requires_third_party", 
            "requires_cost_center",
            "description",
            "notes"
        ]
        
        print(f"📋 Campos encontrados: {field_names}")
        
        missing_fields = []
        for field in expected_fields:
            if field not in field_names:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Campos faltantes: {missing_fields}")
            return False
        else:
            print("✅ Todos los campos esperados están presentes")
        
        # Verificar el campo allows_reconciliation específicamente
        reconciliation_field = next(
            (field for field in account_metadata.fields 
             if field.internal_name == "allows_reconciliation"), 
            None
        )
        
        if reconciliation_field:
            print(f"✅ Campo allows_reconciliation encontrado:")
            print(f"   - Label: {reconciliation_field.display_label}")
            print(f"   - Tipo: {reconciliation_field.field_type}")
            print(f"   - Default: {reconciliation_field.default_value}")
            print(f"   - Descripción: {reconciliation_field.description}")
        else:
            print("❌ Campo allows_reconciliation no encontrado")
            return False
        
        # Verificar el campo category
        category_field = next(
            (field for field in account_metadata.fields 
             if field.internal_name == "category"), 
            None
        )
        
        if category_field and category_field.choices:
            print(f"✅ Campo category encontrado con {len(category_field.choices)} opciones:")
            for choice in category_field.choices[:3]:  # Mostrar solo las primeras 3
                print(f"   - {choice['value']}: {choice['label']}")
            if len(category_field.choices) > 3:
                print(f"   ... y {len(category_field.choices) - 3} más")
        else:
            print("❌ Campo category no encontrado o sin opciones")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error obteniendo metadata: {e}")
        return False


async def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de importación de cuentas...")
    
    # Test 1: Verificar metadata
    success = await test_account_metadata()
    
    if success:
        print("\n✅ ¡Todas las pruebas pasaron exitosamente!")
        print("📥 El sistema está listo para importar cuentas con:")
        print("   - Campo allows_reconciliation")
        print("   - Categorías de cuentas")
        print("   - Categorías de flujo de efectivo")
        print("   - Configuraciones de terceros y centros de costo")
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
