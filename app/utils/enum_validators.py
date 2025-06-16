"""
Utilidades para validación de enums case-insensitive
"""
from typing import Any, Type, Optional
from enum import Enum


def validate_enum_case_insensitive(value: Any, enum_class: Type[Enum]) -> Optional[Enum]:
    """
    Valida un enum de forma case-insensitive.
    
    Args:
        value: El valor a validar (puede ser string, enum, etc.)
        enum_class: La clase enum a usar para validación
        
    Returns:
        El valor del enum correspondiente
        
    Raises:
        ValueError: Si el valor no corresponde a ningún valor del enum
    """
    if value is None:
        return None
        
    # Si ya es una instancia del enum, retornarlo
    if isinstance(value, enum_class):
        return value
    
    # Si es un string, hacer comparación case-insensitive
    if isinstance(value, str):
        value_lower = value.lower().strip()
        
        # Buscar coincidencia case-insensitive
        for enum_item in enum_class:
            if enum_item.value.lower() == value_lower:
                return enum_item
                
        # Si no se encuentra, listar valores válidos para el error
        valid_values = [item.value for item in enum_class]
        raise ValueError(f"Invalid value '{value}' for {enum_class.__name__}. Valid values are: {valid_values}")
    
    # Si no es string ni enum, intentar convertir a string y validar
    try:
        return validate_enum_case_insensitive(str(value), enum_class)
    except Exception:
        valid_values = [item.value for item in enum_class]
        raise ValueError(f"Invalid value '{value}' for {enum_class.__name__}. Valid values are: {valid_values}")


def create_enum_validator(enum_class: Type[Enum]):
    """
    Crea un validador de campo para Pydantic que maneja enums case-insensitive.
    
    Args:
        enum_class: La clase enum a validar
        
    Returns:
        Función validadora para usar con @field_validator
    """
    def validator(value: Any) -> Optional[Enum]:
        return validate_enum_case_insensitive(value, enum_class)
    
    return validator
