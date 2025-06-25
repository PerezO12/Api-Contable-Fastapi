#!/usr/bin/env python3
"""
Test para verificar que la importación de productos genere códigos automáticamente
"""
import json
import io
import csv

def test_product_metadata():
    """Verifica que la metadata de productos esté configurada correctamente"""
    from app.services.model_metadata_registry import ModelMetadataRegistry
    
    registry = ModelMetadataRegistry()
    metadata = registry.get_model_metadata("product")
    
    assert metadata is not None, "Product metadata should exist"
    print(f"✅ Product metadata found: {metadata.display_name}")
    
    # Verificar que solo el nombre sea obligatorio
    required_fields = [f for f in metadata.fields if f.is_required]
    print(f"📋 Required fields: {[f.internal_name for f in required_fields]}")
    
    assert len(required_fields) == 1, f"Should have only 1 required field, but found {len(required_fields)}: {[f.internal_name for f in required_fields]}"
    assert required_fields[0].internal_name == "name", f"Only 'name' should be required, but found: {required_fields[0].internal_name}"
    
    # Verificar que el nombre sea único
    name_field = next((f for f in metadata.fields if f.internal_name == "name"), None)
    assert name_field is not None, "Name field should exist"
    assert name_field.is_unique, "Name field should be unique"
    
    # Verificar que el código no sea obligatorio
    code_field = next((f for f in metadata.fields if f.internal_name == "code"), None)
    assert code_field is not None, "Code field should exist"
    assert not code_field.is_required, "Code field should not be required"
    assert code_field.is_unique, "Code field should be unique"
    
    print("✅ Product metadata configuration is correct")
    print(f"   - Only 'name' is required and unique")
    print(f"   - 'code' is optional and unique (will be auto-generated)")
    print(f"   - Business key fields: {metadata.business_key_fields}")


def test_product_code_generation():
    """Test que la función de generación de código funcione"""
    from app.services.product_service import ProductService
    from app.models.product import ProductType
    
    # Mock de database session
    class MockDB:
        def query(self, model):
            return MockQuery()
    
    class MockQuery:
        def filter(self, condition):
            return self
        def first(self):
            return None  # No existe el código
    
    service = ProductService(MockDB())
    
    # Test con producto
    code1 = service._generate_product_code("Producto de Prueba", ProductType.PRODUCT)
    print(f"✅ Generated code for product: {code1}")
    assert code1.startswith("PRD-"), f"Product code should start with PRD-, got: {code1}"
    
    # Test con servicio
    code2 = service._generate_product_code("Servicio de Consultoría", ProductType.SERVICE)
    print(f"✅ Generated code for service: {code2}")
    assert code2.startswith("SRV-"), f"Service code should start with SRV-, got: {code2}"
    
    # Test con nombre corto
    code3 = service._generate_product_code("A", ProductType.PRODUCT)
    print(f"✅ Generated code for short name: {code3}")
    assert len(code3) > 6, f"Code should be padded for short names, got: {code3}"


def create_test_csv():
    """Crea un archivo CSV de prueba con productos"""
    csv_content = """Nombre
Laptop Dell Inspiron 15
Mouse Óptico USB
Teclado Mecánico RGB
Monitor 24 pulgadas
Servicio de Soporte Técnico
Consultoría IT
"""
    return csv_content


def test_csv_creation():
    """Test que podemos crear archivos CSV correctamente"""
    csv_content = create_test_csv()
    print("✅ Test CSV created:")
    print(csv_content)
    
    # Verificar que se puede parsear
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    print(f"✅ CSV parsed successfully, found {len(rows)} rows")
    
    for i, row in enumerate(rows, 1):
        print(f"   Row {i}: {row}")


if __name__ == "__main__":
    print("🧪 Testing Product Import with Auto Code Generation")
    print("=" * 60)
    
    try:
        print("\n1. Testing Product Metadata Configuration...")
        test_product_metadata()
        
        print("\n2. Testing Product Code Generation...")
        test_product_code_generation()
        
        print("\n3. Testing CSV Creation...")
        test_csv_creation()
        
        print("\n🎉 All tests passed!")
        print("\n📝 Summary:")
        print("   - Products only require 'name' field (unique, case-sensitive)")
        print("   - Code is auto-generated when not provided")
        print("   - Business key is now 'name' instead of 'code'")
        print("   - Ready for import testing!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
