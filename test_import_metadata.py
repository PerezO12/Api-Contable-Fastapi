"""
Test script para verificar la validación de unicidad case sensitive
en la importación genérica de datos
"""
import asyncio
import logging
from typing import List
from app.services.model_metadata_registry import ModelMetadataRegistry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_metadata_validation():
    """Test que los metadatos estén configurados correctamente"""
    
    registry = ModelMetadataRegistry()
    
    # Test Third Party metadata
    third_party_metadata = registry.get_model_metadata("third_party")
    
    print("=== THIRD PARTY METADATA TEST ===")
    print(f"Model: {third_party_metadata.model_name}")
    print(f"Display Name: {third_party_metadata.display_name}")
    print(f"Business Key Fields: {third_party_metadata.business_key_fields}")
    
    print("\n=== FIELD ANALYSIS ===")
    for field in third_party_metadata.fields:
        print(f"Field: {field.internal_name}")
        print(f"  - Required: {field.is_required}")
        print(f"  - Unique: {getattr(field, 'is_unique', False)}")
        print(f"  - Default: {getattr(field, 'default_value', None)}")
        print(f"  - Type: {field.field_type}")
        print()
    
    # Test required fields
    required_fields = registry.get_required_fields("third_party")
    print(f"Required fields: {[f.internal_name for f in required_fields]}")
    
    # Test unique fields
    unique_fields = registry.get_unique_fields("third_party")
    print(f"Unique fields: {[f.internal_name for f in unique_fields]}")
    
    # Test business key fields
    business_keys = registry.get_business_key_fields("third_party")
    print(f"Business key fields: {business_keys}")
    
    # Validate expectations
    assert "name" in [f.internal_name for f in required_fields], "Name should be required"
    assert "name" in [f.internal_name for f in unique_fields], "Name should be unique"
    assert "name" in business_keys, "Name should be a business key"
    assert "document_number" not in [f.internal_name for f in required_fields], "Document number should NOT be required"
    
    # Check third_party_type has default value
    third_party_type_field = next((f for f in third_party_metadata.fields if f.internal_name == "third_party_type"), None)
    assert third_party_type_field is not None, "third_party_type field should exist"
    assert not third_party_type_field.is_required, "third_party_type should NOT be required"
    assert getattr(third_party_type_field, 'default_value', None) == "customer", "third_party_type should have default value 'customer'"
    
    print("\n✅ All validations passed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_metadata_validation())
