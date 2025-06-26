#!/usr/bin/env python3
"""
Test para verificar que los metadatos del modelo Product están correctos
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.model_metadata_registry import model_registry

def test_product_metadata():
    """Verifica que los metadatos del modelo Product sean correctos"""
    
    # Obtener metadatos del modelo Product
    product_metadata = model_registry.get_model_metadata('product')
    
    print('===== METADATOS DEL MODELO PRODUCT =====')
    print(f'Nombre del modelo: {product_metadata.model_name}')
    print(f'Tabla: {product_metadata.table_name}')
    print(f'Campos clave de negocio: {product_metadata.business_key_fields}')
    print()

    print('===== CAMPOS OBLIGATORIOS =====')
    required_fields = [f for f in product_metadata.fields if f.is_required]
    for field in required_fields:
        print(f'- {field.internal_name}: {field.display_label}')
    print()

    print('===== VERIFICAR QUE NO EXISTE is_active =====')
    has_is_active = any(f.internal_name == 'is_active' for f in product_metadata.fields)
    print(f'¿Tiene campo is_active? {has_is_active}')

    if has_is_active:
        is_active_field = next(f for f in product_metadata.fields if f.internal_name == 'is_active')
        print(f'❌ ERROR: Campo is_active encontrado: {is_active_field.display_label}')
        return False
    else:
        print('✅ CORRECTO: No hay campo is_active en Product')
    
    print()
    print('===== CAMPOS CON is_active EN EL SISTEMA =====')
    for model_name in model_registry.get_available_models():
        model_meta = model_registry.get_model_metadata(model_name)
        for field in model_meta.fields:
            if field.internal_name == 'is_active':
                print(f'- Modelo {model_name}: campo is_active ({field.display_label})')
    
    return True

if __name__ == "__main__":
    test_product_metadata()
